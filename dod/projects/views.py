from django.db import transaction
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
import datetime
from rest_framework.views import APIView
from products.serializers import ProductCreateSerializer
from projects.models import Project
from projects.serializers import ProjectCreateSerializer, ProjectDepositInfoRetrieveSerializer, ProjectUpdateSerializer, \
    ProjectDashboardSerializer, SimpleProjectInfoSerializer, ProjectLinkSerializer
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
        pass

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

    def update(self, request, *args, **kwargs):
        """
        프로젝트 업데이트 api
        name, created_at, dead_at 중 원하는 데이터 입력하여 PUT 요청하면 됨
        * 상품의 관련된 수정은 구현하지 않음 ex: 상품바꾸기, 상품 추가하기(winner_count), 환불하기 등 (문의하기로 처리)
        api: api/v1/project/<id>
        method : PUT
        :data:
        {'created_at', 'dead_at', 'name'}
        :return: {'id', 'name'', 'total_price'}
        """
        return super(ProjectViewSet, self).update(request, args, kwargs)

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
        pagination 됨.
        :return
        {
        "count", "next", "previous",
        "results": [
                        {"id", "name", "total_respondent",
                        "products":
                                [
                                "id", "item_thumbnail", "present_winner_count", "winner_count"
                                ],
                        "dead_at", "is_done", "status"
                        },
                        {
                        ...
                        }
                    ]
        }
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


class LinkRouteAPIView(APIView):
    permission_classes = [AllowAny]
    """
    클라에서 이 링크로 접속하면 핸드폰 인증 페이지를 띄움.
    또는 추후 html로 한다면, 이 링크로 접속시 해당 html 띄워야 함(Template 처럼)
    현재는 클라에서 호스팅한다는 가정 하에
    """
    def get(self, request, *args, **kwargs):
        """
        api : /link/<slug>
        return : {'id', 'dead_at', 'is_started', 'is_done', 'status'}
        시작되지 않았을때, 종료되었을 때, 결제 승인이 되지 않았을 때 접속시 페이지 기획이 필요합니다.
        """
        project_hash_key = kwargs['slug']
        project = Project.objects.filter(project_hash_key=project_hash_key).last()
        if not project:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = SimpleProjectInfoSerializer(project)
        return Response(serializer.data, status=status.HTTP_200_OK)