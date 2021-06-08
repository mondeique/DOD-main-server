from django.db import transaction
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from products.serializers import ProductCreateSerializer
from projects.models import Project
from projects.serializers import ProjectCreateSerializer, ProjectDepositInfoRetrieveSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ]
    queryset = Project.objects.all().select_related('owner')

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        elif self.action in 'update':
            return None
        elif self.action == 'retrieve':
            return None
        elif self.action == '_create_products':
            return ProductCreateSerializer
        else:
            return super(ProjectViewSet, self).get_serializer_class()

    # @action(methods=['post'], detail=False)
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        :data:
        {'winner_count', 'created_at', 'dead_at', 'item'}
        :return: {'id', 'name', 'winner_count', 'total_price'}
        """
        data = request.data.copy()

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        project = serializer.save()

        self.product_data = {
            'item': data.get('item'),
            'count': data.get('winner_count'),
            'project': project.id
        }
        self._create_products()

        project_info_serializer = ProjectDepositInfoRetrieveSerializer(project)
        return Response(project_info_serializer.data, status=status.HTTP_201_CREATED)

    def _create_products(self):
        serializer = ProductCreateSerializer(data=self.product_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()


    def update(self, request, *args, **kwargs):
        pass