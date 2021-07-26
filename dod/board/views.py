from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from board.models import Board
from core.permissions import BoardViewPermission
from projects.models import Project
from board.serializers import BoardCreateSerializer, BoardUpdateSerializer, BoardListSerializer, BoardInfoSerializer
from core.pagination import DodPagination
from urllib.request import urlopen
from bs4 import BeautifulSoup
import time


def _google_info_crawler(form_url):
    try:
        html = urlopen(form_url)
        source = BeautifulSoup(html, 'html.parser')
        dod_html = source.find_all('script', type='text/javascript')
        dod_html_link = dod_html[-1]

        string_html = str(dod_html_link)
        list_html = string_html.split('https://d-o-d.io/checklink')
        hash_key = list_html[1].split('/')[1]
        time.sleep(2)
    except Exception:
        hash_key = None
    return hash_key


class BoardViewSet(viewsets.ModelViewSet):
    permission_classes = [BoardViewPermission, ]
    queryset = Board.objects.filter(is_active=True)

    def get_serializer_class(self):
        if self.action == 'create':
            return BoardCreateSerializer
        elif self.action in 'update':
            return BoardUpdateSerializer
        elif self.action in 'retrieve':
            return BoardInfoSerializer
        elif self.action in 'list':
            return BoardListSerializer
        else:
            return super(BoardViewSet, self).get_serializer_class()

    @action(methods=['post'], detail=False)
    def check_dod(self, request, *args, **kwargs):
        """
        api: api/v1/board/check_dod/
        method : POST
        data: {'form_link'}
        return : {'is_dod', 'project_id'}
        """
        google_form_link = request.data.get('form_link')
        is_dod = False
        project_id = None
        project_hask_key = _google_info_crawler(google_form_link)
        if Project.objects.filter(owner=request.user, project_hash_key=project_hask_key).exists():
            is_dod = True
            project_id = Project.objects.get(owner=request.user, project_hask_key=project_hask_key).id
        return Response({"is_dod": is_dod, "project_id": project_id})

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        api: api/v1/board/
        method : POST
        :data:
        {'form_link', 'title', 'content', 'project'}
        :return: HTTP response
        """
        return super(BoardViewSet, self).create(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        게시 업데이트 api
        title content 중 하나 바꿔 PUT 요청하면 됨
        api: api/v1/board/<id>/
        method : PUT
        :data:
        {'title', 'content'}
        :return: status
        """
        return super(BoardViewSet, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        프로젝트 삭제 api
        api: api/v1/board/<id>
        method : DELETE
        """
        user = request.user
        instance = self.get_object()
        if instance.owner != user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        """
        api: api/v1/board/
        method: GET
        :return
        [
        ]

        """
        paginator = DodPagination()
        page = paginator.paginate_queryset(self.get_queryset(), request)
        serializer = self.get_serializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        api: api/v1/board/<pk>
        method: GET
        pagination 안됨(조회이기 떄문).
        """
        return super(BoardViewSet, self).retrieve(request, args, kwargs)
