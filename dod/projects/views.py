import random
from operator import itemgetter

from django.db import transaction
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
import datetime
from rest_framework.views import APIView
from core.slack import deposit_temp_slack_message
from payment.Bootpay import BootpayApi
from payment.loader import load_credential
from payment.models import UserDepositLog, PaymentErrorLog
from payment.serializers import PaymentCancelSerialzier
from products.models import Item, CustomGifticon, Product
from products.serializers import ProductCreateSerializer, CustomGifticonCreateSerializer
from projects.models import Project, ProjectMonitoringLog
from projects.serializers import ProjectCreateSerializer, ProjectDepositInfoRetrieveSerializer, ProjectUpdateSerializer, \
    ProjectDashboardSerializer, SimpleProjectInfoSerializer, ProjectLinkSerializer, PastProjectSerializer, \
    ProjectGifticonSerializer
from random import sample
from logic.models import UserSelectLogic, DateTimeLotteryResult, DODAveragePercentage, PercentageResult
from rest_framework import exceptions


def _convert_dict_to_tuple(dic):
    tuple_list = []
    for _, v in enumerate(dic):
        temp_tuple = []
        for key, val in v.items():
            temp_tuple.append(val)
        temp_tuple = tuple(temp_tuple)
        tuple_list.append(temp_tuple)
    return tuple_list


def _sum_same_tuple_first_values(tuple_list):
    d = {q: 0 for q, _ in tuple_list}
    for name, num in tuple_list:
        d[name] += num
    val = list(map(tuple, d.items()))
    return val


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ]
    queryset = Project.objects.all().select_related('owner')

    def __init__(self, *args, **kwargs):
        super(ProjectViewSet, self).__init__(*args, **kwargs)
        self.data = None
        self.files = None
        self.serializer = None
        self.products = None
        self.project = None
        self.custom_upload = None

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        elif self.action in ['update', 'add_gifticons']:
            return ProjectUpdateSerializer
        elif self.action == 'retrieve':
            return None
        elif self.action == '_create_products':
            return ProductCreateSerializer
        elif self.action == 'link_notice':
            return ProjectLinkSerializer
        else:
            return super(ProjectViewSet, self).get_serializer_class()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        api: api/v1/project
        method : POST
        :data:
        1. payment
            {'start_at', 'dead_at',
                items':
                    [{'item':'item.id', 'count':'3'}, {'item':'', 'count':''}]
            }
        2. custom upload
            {'start_at', 'dead_at',
                'custom_upload':
                    ['...1.jpg', '...2.jpg']
            }
        :return: {'id', 'name', 'winner_count', 'total_price'}
        """
        self.data = request.data.copy()
        self.files = request.FILES
        self.data['start_at'] = datetime.datetime.strptime(self.data['start_at'], '%Y/%m/%d')
        self.data['dead_at'] = datetime.datetime.strptime(self.data['dead_at'], '%Y/%m/%d')

        serializer = self.get_serializer_class()
        serializer = serializer(data=self.data, context={'request': request,
                                                         'user': request.user})
        serializer.is_valid(raise_exception=True)
        self.project = serializer.save()
        self._create_project_monitoring_log()

        # UPDATED 20210725 custom upload
        if self.files.get('custom_upload'):
            self.custom_upload = self.files.pop('custom_upload')
            self._create_custom_gifticon()
            self._generate_percentage()

        elif self.data.get('items'):
            self._create_products()
            # self._generate_lucky_time()  # [DEPRECATED] 20210725 not use lucky time
            self._generate_percentage()
            # self._check_undefined_projects() # UPDATED 20210725 not use deposit logs

        else:
            # UPDATED 20210829 onboarding
            # 상품 없어도 생성 됨
            self.project.is_active = True
            self.project.save()

        project_info_serializer = ProjectDepositInfoRetrieveSerializer(self.project)
        return Response(project_info_serializer.data, status=status.HTTP_201_CREATED)

    def _create_custom_gifticon(self):
        item = Item.objects.get(order=999)

        for img in self.custom_upload:
            data = {
                    'item': item.id,
                    'project': self.project.id,
                    'gifticon_img': img
                }
            serializer = CustomGifticonCreateSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        self.project.winner_count = len(self.custom_upload)
        self.project.status = True
        self.project.is_active = True
        self.project.save()

    def _create_products(self):
        items = self.data.get('items')
        if not items:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        winner_count = 0
        for val in items:
            winner_count += val.get('count')
            item_id = val.get('item')
            pay_price = Item.objects.get(pk=item_id).price

            for i in range(val.get('count')):
                # UPDATED 2021.07.04
                # 결제가 붙으면서 업데이트함.
                self.product_data = {
                    'item': item_id,
                    'project': self.project.id,
                    'price': pay_price
                }
                serializer = ProductCreateSerializer(data=self.product_data)
                serializer.is_valid(raise_exception=True)
                serializer.save()

        self.project.winner_count = winner_count
        self.project.save()

    def _create_project_monitoring_log(self):
        ProjectMonitoringLog.objects.create(project=self.project)

    def _create_user_deposit_log(self):
        UserDepositLog.objects.create(project=self.project, total_price=self._calculate_total_price())

    def _check_undefined_projects(self):
        user = self.request.user
        undefined_projects = user.projects.filter(is_active=True).filter(deposit_logs__depositor__isnull=True)
        undefined_projects.update(is_active=False)

    def _calculate_total_price(self):
        counts = self.project.products.all().values_list('count', flat=True)
        if not all(i == 1 for i in counts):
            # Before Payment
            prices = self.project.products.all().values_list('item__price', flat=True)
            mul_price = list(map(lambda x, y: x * y, counts, prices))
            total_price = 0
            for i in mul_price:
                total_price += int(i)
        else:
            # UPDATED 2021.07.04
            # Payment Attached
            products_price = self.project.products.all().values_list('price', flat=True)
            total_price = sum(products_price)

        return total_price

    def _generate_lucky_time(self):
        # project 생성과 동시에 당첨 logic 자동 생성
        # [DEPRECATED] 20210725 logic -> percentage 2-5%
        logic = UserSelectLogic.objects.create(kind=1, project=self.project)
        renewal_dead_at = self.project.start_at + datetime.timedelta(days=4)  # 2021.07.07 [d-o-d.io 리뉴얼 ]추가 : 앞쪽에 몰기 ####
        now = datetime.datetime.now()
        dt_hours = int((renewal_dead_at - self.project.start_at).total_seconds() / 60 / 60)
        random_hours = sorted(sample(range(0, dt_hours), self.project.winner_count))
        bulk_datetime_lottery_result = []
        for i in range(len(random_hours)):
            bulk_datetime_lottery_result.append(DateTimeLotteryResult(
                lucky_time=now + datetime.timedelta(hours=random_hours[i]),
                logic=logic
            ))
        DateTimeLotteryResult.objects.bulk_create(bulk_datetime_lottery_result)

    def _generate_percentage(self):
        # UPDATED 20210725 logic -> percentage
        logic = UserSelectLogic.objects.create(kind=3, project=self.project)
        total_counts = self.project.winner_count
        dod_average_percentage = DODAveragePercentage.objects.last().average_percentage
        average = dod_average_percentage * 10
        for i in range(total_counts):
            # dod 평균확률 +- 1%
            percentage = round(random.randint(abs(average-10), abs(average+10))/1000*100, 2)
            PercentageResult.objects.create(
                percentage=percentage,
                logic=logic
            )

    def _last_day_random_hour(self):
        return sample(range(1, 25), 1)[0]

    @transaction.atomic
    @action(methods=['post'], detail=True)
    def add_gifticons(self, request, *args, **kwargs):
        """
        [UPDATED] 20210829
        온보딩 경험 향상을 위해 상품 없이도 추첨 생성 가능
        이후 기프티콘 추가시 사용하는 api

          api: api/v1/project/add_gifticons/<id>
          method : POST
          :data:
          1. payment
              {'start_at', 'dead_at',
                  items':
                      [{'item':'item.id', 'count':'3'}, {'item':'', 'count':''}]
              }
          2. custom upload
              {'start_at', 'dead_at',
                  'custom_upload':
                      ['...1.jpg', '...2.jpg']
              }
          :return: {'id', 'name', 'winner_count', 'total_price'}
          """
        self.data = request.data.copy()
        self.files = request.FILES
        self.project = self.get_object()

        if self.project.products.exists():
            self.project.products.all().delete()

        if self.files.get('custom_upload'):
            self.custom_upload = self.files.pop('custom_upload')
            self._create_custom_gifticon()
            self._generate_percentage()
        else:
            self._create_products()
            self._generate_percentage()

        project_info_serializer = ProjectDepositInfoRetrieveSerializer(self.project)
        return Response(project_info_serializer.data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        프로젝트 업데이트 api
        [DEPRECATED]
        items, start_at, dead_at 중 원하는 데이터 입력하여 PUT 요청하면 됨
        api: api/v1/project/<id>
        method : PUT
        :data:
        {'start_at', 'dead_at', 'items':[]}
        :return: {'id', 'name'', 'total_price'}
        """
        # items = request.data.get('items')
        # print(request.data)
        # if not items:
        #     return Response(status=status.HTTP_400_BAD_REQUEST)
        #
        # self.data = request.data.copy()
        # self.files = request.FILES
        # serializer = self.get_serializer(self.get_object(), data=self.data, partial=True)
        # serializer.is_valid(raise_exception=True)
        # self.project = serializer.save()
        #
        # previous_items = list(self.project.products.values('item', 'count'))
        # previous_items = sorted(previous_items, key=itemgetter('item'))
        #
        # # UPDATED 2021.07.04
        # # Convert list of dict to list of tuple
        # previous_tuple_list = _convert_dict_to_tuple(previous_items)
        # # Sum same item id : [(1,1), (1,1), (2,1)] => [(1,2), (2,1)]
        # previous_items = _sum_same_tuple_first_values(previous_tuple_list)
        #
        # present_tuple_list = _convert_dict_to_tuple(sorted(items, key=itemgetter('item')))
        # present_items = _sum_same_tuple_first_values(present_tuple_list)
        #
        # if previous_items == present_items:
        #     # item 변화 없는 경우
        #     project_info_serializer = ProjectDepositInfoRetrieveSerializer(self.project)
        #     return Response(project_info_serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
        # else:
        #     # delete previous data
        #     self.project.products.all().delete()
        #     self.project.select_logics.all().delete()
        #     # self.project.deposit_logs.all().delete()
        #     # create new data
        #
        #     # UPDATED 20210725 custom upload
        #     if self.data.get('custom_upload'):
        #         self.custom_upload = self.files.pop('custom_upload')
        #         self._create_custom_gifticon()
        #         self._generate_percentage()
        #         project_info_serializer = ProjectDepositInfoRetrieveSerializer(self.project)
        #
        #     else:
        #         self._create_products()
        #         # self._generate_lucky_time()  # [DEPRECATED] 20210725 not use lucky time
        #         self._generate_percentage()
        #         # self._check_undefined_projects() # UPDATED 20210725 not use deposit logs
        #         project_info_serializer = ProjectDepositInfoRetrieveSerializer(self.project)
        #
        #     return Response(project_info_serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)

        self.data = request.data.copy()
        self.files = request.FILES
        self.data['start_at'] = datetime.datetime.strptime(self.data['start_at'], '%Y/%m/%d')
        self.data['dead_at'] = datetime.datetime.strptime(self.data['dead_at'], '%Y/%m/%d')

        serializer = self.get_serializer_class()
        serializer = serializer(self.get_object(), data=self.data, context={'request': request,
                                                         'user': request.user}, partial=True)
        serializer.is_valid(raise_exception=True)
        self.project = serializer.save()

        if self.project.products.exists():
            self.project.products.all().delete()

        # UPDATED 20210725 custom upload
        if self.files.get('custom_upload'):
            self.custom_upload = self.files.pop('custom_upload')
            self._create_custom_gifticon()
            self._generate_percentage()

        elif self.data.get('items'):
            self._create_products()
            # self._generate_lucky_time()  # [DEPRECATED] 20210725 not use lucky time
            self._generate_percentage()
            # self._check_undefined_projects() # UPDATED 20210725 not use deposit logs

        else:
            # UPDATED 20210829 onboarding
            # 상품 없어도 생성 됨
            self.project.is_active = True
            self.project.save()

        project_info_serializer = ProjectDepositInfoRetrieveSerializer(self.project)
        return Response(project_info_serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)

    @action(methods=['get'], detail=True)
    def link_notice(self, request, *args, **kwargs):
        """
        링크안내 페이지
        api: api/v1/project/<id>/link_notice
        :return: {
            "url" ,
            "link_notice" : {"id", "title", "pc_url", "mobile_url"}
        }
        """
        project = self.get_object()
        serializer = self.get_serializer(project)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def deletable(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()
        if instance.owner != user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if instance.products.filter(rewards__winner_id__isnull=False).exists() or \
                instance.custom_gifticons.filter(winner_id__isnull=False).exists():
            return Response({'deletable': False})
        else:
            return Response({'deletable': True})

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """
        프로젝트 삭제 api
        api: api/v1/project/<id>
        method : DELETE
        """
        user = request.user
        instance = self.get_object()
        if instance.owner != user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if instance.respondents.exists():
            return Response(status=status.HTTP_403_FORBIDDEN)

        instance.is_active = False
        instance.save()

        if instance.payments.exists():
            payment = instance.payments.last()
            bootpay = self.get_access_token()
            result = bootpay.cancel(payment.receipt_id, '{}'.format(payment.price), '디오디', '결제취소')
            if result['status'] != 200:
                error_data = {
                    'kind': 10,
                    'user': user,
                    'temp_payment': payment,
                    'description': '유저 결제취소 실패',
                    'bootpay_receipt_id' : payment.receipt_id
                }
                PaymentErrorLog.objects.create(**error_data)
                # 결제취소실패
                payment.status = -20
                payment.save()

                return Response(status=status.HTTP_204_NO_CONTENT)

            serializer = PaymentCancelSerialzier(payment, data=result['data'])
            # 결제취소진행중
            payment.status = -30
            payment.save()

            if serializer.is_valid():
                serializer.save()

                # trade : bootpay 환불 완료
                Product.objects.filter(project__payments=payment).update(status=2)  # 결제되었다가 취소이므로 환불.

                # payment : 결제 취소 완료
                payment.status = 20
                payment.save()

            else:
                PaymentErrorLog.objects.create(user=request.user, temp_payment=payment,
                                               description='유저 결제취소 실패',
                                               bootpay_receipt_id=payment.receipt_id)

                # 결제취소실패
                payment.status = -20
                payment.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def get_access_token():
        secrets = load_credential("bootpay", "")
        bootpay = BootpayApi(application_id=secrets["rest_application_id"],
                             private_key=secrets["private_key"])
        result = bootpay.get_access_token()
        if result['status'] is 200:
            return bootpay
        else:
            raise exceptions.APIException(detail='bootpay access token 확인바람')

    @action(methods=['put'], detail=True)
    def depositor(self, request, *args, **kwargs):
        """
        [DEPRECATED] 2021.07.04
        """
        project = self.get_object()
        if project.owner != request.user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        depositor = request.data.get('depositor')
        if not depositor:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        project.deposit_logs.update(depositor=depositor)
        project.is_active = True
        project.save()
        message = "\n [입금자명을 입력했습니다.] \n" \
                  "전화번호: {} \n" \
                  "입금자명: {}\n" \
                  "결제금액: {}원\n" \
                  "검색 키: {}\n" \
                  "--------------------".format(project.owner.phone,
                                                project.deposit_logs.first().depositor,
                                                project.deposit_logs.first().total_price,
                                                project.project_hash_key)
        deposit_temp_slack_message(message)
        return Response(status=status.HTTP_206_PARTIAL_CONTENT)

    @action(methods=['put'], detail=True)
    def set_name(self, request, *args, **kwargs):
        """
        추첨링크(프로젝트)명 변경하는 api
        """
        project = self.get_object()
        if project.owner != request.user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        name = request.data.get('name')
        if not name:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        project.name = name
        project.save()
        return Response(status=status.HTTP_206_PARTIAL_CONTENT)


class ProjectDashboardViewSet(viewsets.GenericViewSet,
                              mixins.ListModelMixin,
                              mixins.RetrieveModelMixin):
    permission_classes = [AllowAny, ]
    queryset = Project.objects.filter(is_active=True)
    serializer_class = ProjectDashboardSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return self.queryset.filter(kind=Project.ANONYMOUS)
        queryset = self.queryset.filter(owner=user).order_by('-id')
        return queryset

    def list(self, request, *args, **kwargs):
        """
        api: api/v1/dashboard/
        method: GET
        :return
        [
          {"id", "name", "total_respondent", "progress",
          "dead_at", "start_at", "project_status"
          },
        {
        ...
        }
        ]

        """

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        api: api/v1/dashboard/<pk>
        method: GET
        pagination 안됨(조회이기 떄문).
        """
        return super(ProjectDashboardViewSet, self).retrieve(request, args, kwargs)

    @action(methods=['get'], detail=True)
    def gifticons(self, request, *args, **kwargs):
        project = self.get_object()
        serializer = ProjectGifticonSerializer(project)
        return Response(serializer.data)


class PastProjectViewSet(viewsets.GenericViewSet,
                         mixins.ListModelMixin,
                         mixins.RetrieveModelMixin):
    permission_classes = [IsAuthenticated]
    queryset = Project.objects.filter(is_active=True)
    serializer_class = PastProjectSerializer

    def list(self, request, *args, **kwargs):
        """
        api: api/v1/last-project/
        method: GET
        """
        user = request.user
        now = datetime.datetime.now()
        buffer_day = now - datetime.timedelta(days=2)
        queryset = self.get_queryset().filter(owner=user).filter(dead_at__lte=buffer_day).order_by('-id')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """
        api: api/v1/dashboard/<pk>
        method: GET
        """
        return super(PastProjectViewSet, self).retrieve(request, args, kwargs)


class ProjectValidCheckAPIView(APIView):
    permission_classes = [AllowAny]
    """
    [DEPRECATED] -> Server단에서 referer 체크할때 같이 체크
    클라에서 프로젝트 활성화 여부를 체크하는 api.
    또는 추후 html로 한다면, 이 링크로 접속시 해당 html 띄워야 함(Template 처럼)
    현재는 클라에서 호스팅한다는 가정 하에
    """
    def get(self, request, *args, **kwargs):
        """
        api : /check_link/<slug>
        return : {'id', 'project_status'}
        시작되지 않았을때, 종료되었을 때, 결제 승인이 되지 않았을 때 접속시 페이지 기획이 필요합니다.
        """
        # TODO : Project check & validator check
        project_hash_key = kwargs['slug']
        project = Project.objects.filter(project_hash_key=project_hash_key).last()
        if not project:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = SimpleProjectInfoSerializer(project)
        return Response(serializer.data, status=status.HTTP_200_OK)
