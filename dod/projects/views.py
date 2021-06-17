from operator import itemgetter

from django.db import transaction
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
import datetime
from rest_framework.views import APIView

from core.slack import deposit_temp_slack_message
from payment.models import UserDepositLog
from products.serializers import ProductCreateSerializer
from projects.models import Project
from projects.serializers import ProjectCreateSerializer, ProjectDepositInfoRetrieveSerializer, ProjectUpdateSerializer, \
    ProjectDashboardSerializer, SimpleProjectInfoSerializer, ProjectLinkSerializer, PastProjectSerializer
from random import sample
from logic.models import UserSelectLogic, DateTimeLotteryResult


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ]
    queryset = Project.objects.filter(is_active=True).select_related('owner')

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        elif self.action in 'update':
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
        {'start_at', 'dead_at',
        items': [{'item':'item.id', 'count':'3'}, {'item':'', 'count':''}]}
        :return: {'id', 'name', 'winner_count', 'total_price'}
        """
        self.data = request.data.copy()
        serializer = self.get_serializer(data=self.data)
        serializer.is_valid(raise_exception=True)
        self.project = serializer.save()
        self._create_products()
        self._generate_lucky_time()
        self._create_user_deposit_log()

        project_info_serializer = ProjectDepositInfoRetrieveSerializer(self.project)

        return Response(project_info_serializer.data, status=status.HTTP_201_CREATED)

    def _create_products(self):
        items = self.data.get('items')
        if not items:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        winner_count = 0
        for val in items:
            self.product_data = {
                'item': val.get('item'),
                'count': val.get('count'),
                'project': self.project.id
            }
            winner_count += val.get('count')
            serializer = ProductCreateSerializer(data=self.product_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        self.project.winner_count = winner_count
        self.project.save()

    def _create_user_deposit_log(self):
        UserDepositLog.objects.create(project=self.project, total_price=self._calculate_total_price())

    def _calculate_total_price(self):
        counts = self.project.products.all().values_list('count', flat=True)
        prices = self.project.products.all().values_list('item__price', flat=True)
        mul_price = list(map(lambda x,y: x*y, counts, prices))
        total_price = 0
        for i in mul_price:
            total_price += int(i)
        return total_price

    def _generate_lucky_time(self):
        # project 생성과 동시에 당첨 logic 자동 생성
        logic = UserSelectLogic.objects.create(kind=1, project=self.project)
        dt_hours = int((self.project.dead_at - self.project.start_at).total_seconds() / 60 / 60)
        random_hours = sorted(sample(range(0, dt_hours), self.project.winner_count - 1))
        bulk_datetime_lottery_result = []
        for i in range(len(random_hours)):
            bulk_datetime_lottery_result.append(DateTimeLotteryResult(
                lucky_time=self.project.start_at + datetime.timedelta(hours=random_hours[i]),
                logic=logic
            ))
        DateTimeLotteryResult.objects.bulk_create(bulk_datetime_lottery_result)
        DateTimeLotteryResult.objects.create(
            lucky_time=self.project.dead_at - datetime.timedelta(hours=self._last_day_random_hour()),
            logic=logic
        )

    def _last_day_random_hour(self):
        return sample(range(1, 25), 1)[0]

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        프로젝트 업데이트 api
        TODO name만 따로 업데이트하는 함수
        items, start_at, dead_at 중 원하는 데이터 입력하여 PUT 요청하면 됨
        api: api/v1/project/<id>
        method : PUT
        :data:
        {'start_at', 'dead_at', 'items':[]}
        :return: {'id', 'name'', 'total_price'}
        """
        items = request.data.get('items')
        if not items:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        self.data = request.data.copy()
        serializer = self.get_serializer(self.get_object(), data=self.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.project = serializer.save()

        previous_items = list(self.project.products.values('item', 'count'))
        previous_items = sorted(previous_items, key=itemgetter('item'))
        present_items = sorted(items, key=itemgetter('item'))
        if previous_items == present_items:
            # item 변화 없는 경우
            project_info_serializer = ProjectDepositInfoRetrieveSerializer(self.project)
            return Response(project_info_serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
        else:
            # delete previous data
            self.project.products.all().delete()
            self.project.select_logics.all().delete()
            self.project.deposit_logs.all().delete()
            # create new data
            self._create_products()
            self._generate_lucky_time()
            self._create_user_deposit_log()
            project_info_serializer = ProjectDepositInfoRetrieveSerializer(self.project)
            return Response(project_info_serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)

    @action(methods=['get'], detail=True)
    def link_notice(self, request, *args, **kwargs):
        """
        api: api/v1/project/<id>/link_notice
        :return: {
            "url" ,
            "link_notice" : {"id", "title", "content(html)"}
        }
        """
        project = self.get_object()
        serializer = self.get_serializer(project)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['put'], detail=True)
    def depositor(self, request, *args, **kwargs):
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
                  "--------------------".format(project.owner.phone,
                                                project.deposit_logs.first().depositor,
                                                project.deposit_logs.first().total_price)
        deposit_temp_slack_message(message)
        return Response(status=status.HTTP_206_PARTIAL_CONTENT)

    @action(methods=['put'], detail=True)
    def set_name(self, request, *args, **kwargs):
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
    permission_classes = [IsAuthenticated, ]
    queryset = Project.objects.filter(is_active=True)
    serializer_class = ProjectDashboardSerializer

    def list(self, request, *args, **kwargs):
        """
        api: api/v1/dashboard/
        method: GET
        :return
        [
          {"id", "name", "total_respondent",
            "products":[
                        {"id", "item_thumbnail", "present_winner_count", "winner_count"},
                         {}
                       ],
          "dead_at", "start_at", "project_status"
          },
        {
        ...
        }
        ]

        """
        user = request.user
        now = datetime.datetime.now()
        buffer_day = now - datetime.timedelta(days=2)
        queryset = self.get_queryset().filter(owner=user).filter(dead_at__gte=buffer_day).order_by('-id')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """
        api: api/v1/dashboard/<pk>
        method: GET
        pagination 안됨(조회이기 떄문).
        """
        return super(ProjectDashboardViewSet, self).retrieve(request, args, kwargs)


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
    클라에서 프로젝트 활성화 여부를 체크하는 api.
    또는 추후 html로 한다면, 이 링크로 접속시 해당 html 띄워야 함(Template 처럼)
    현재는 클라에서 호스팅한다는 가정 하에
    """
    def get(self, request, *args, **kwargs):
        """
        api : /check_link/<slug>
        return : {'id', 'dead_at', 'is_started', 'is_done', 'status'}
        시작되지 않았을때, 종료되었을 때, 결제 승인이 되지 않았을 때 접속시 페이지 기획이 필요합니다.
        """
        project_hash_key = kwargs['slug']
        project = Project.objects.filter(project_hash_key=project_hash_key).last()
        if not project:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = SimpleProjectInfoSerializer(project)
        return Response(serializer.data, status=status.HTTP_200_OK)
