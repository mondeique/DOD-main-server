from operator import itemgetter

from django.db import transaction
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from board.models import Board
from projects.models import Project
from board.serializers import BoardCreateSerializer, BoardUpdateSerializer, BoardMainSerializer, BoardInfoSerializer
from core.pagination import DodPagination

from urllib.request import urlopen
from urllib import error
from requests.exceptions import ConnectionError
from urllib3.exceptions import NewConnectionError, MaxRetryError
from bs4 import BeautifulSoup
import time


def _google_info_crawler(form_url):
    try:
        html = urlopen(form_url)
        source = BeautifulSoup(html, 'html.parser')
        dod_html = source.find_all('script', type='text/javascript')
        dod_html_link = dod_html[-1]

        string_html = str(dod_html_link)
        hash_key = ''
        list_html = string_html.split('https://d-o-d.io/checklink')
        hash_key = list_html[1].split('/')[1]
        time.sleep(2)
    except (ConnectionResetError, error.URLError, error.HTTPError, ConnectionRefusedError,
            ConnectionError, NewConnectionError, MaxRetryError):
        print("Connection Error")
    return hash_key


class BoardViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ]
    queryset = Board.objects.filter(is_active=True)

    def get_serializer_class(self):
        if self.action == 'create':
            return BoardCreateSerializer
        elif self.action in 'update':
            return BoardUpdateSerializer
        elif self.action in 'retrieve':
            return BoardInfoSerializer
        elif self.action in 'list':
            return BoardMainSerializer
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
    @action(methods=['post'], detail=False)
    def create(self, request, *args, **kwargs):
        """
        api: api/v1/board
        method : POST
        :data:
        {'form_link', 'title', 'content', 'project'}
        :return: HTTP response
        """
        self.data = request.data.copy()
        serializer = self.get_serializer_class()
        serializer = serializer(data=self.data, context={'request': request,
                                                         'user': request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_201_CREATED)

    @transaction.atomic
    @action(methods=['put'], detail=True)
    def update(self, request, *args, **kwargs):
        """
        게시 업데이트 api
        title content 중 하나 바꿔 PUT 요청하면 됨
        api: api/v1/board/<id>
        method : PUT
        :data:
        {'title', 'content'}
        :return: status
        """
        # self.data = request.data.copy()
        # serializer = self.get_serializer(self.get_object(), data=self.data, partial=True)
        # serializer.is_valid(raise_exception=True)
        # serializer.save()
        # return Response(status=status.HTTP_206_PARTIAL_CONTENT)
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

    @action(permission_classes = [AllowAny], methods=['get'], detail=False)
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

    @action(permission_classes = [AllowAny], methods=['get'], detail=True)
    def retrieve(self, request, *args, **kwargs):
        """
        api: api/v1/board/<pk>
        method: GET
        pagination 안됨(조회이기 떄문).
        """
        return super(BoardViewSet, self).retrieve(request, args, kwargs)


class BoardDODCheckAPIView(APIView):
    permission_classes = [IsAuthenticated]
    """
    google form 이 DOD 링크가 붙어있는 설문인지 아닌지 구분해내는 API 입니다. 
    DOD 여부와 함께 해당 project 의 id를 제공합니다. 해당 id 가 존재하지 않을 경우 None 
    """
    def post(self, request, *args, **kwargs):
        """
        api: api/v1/check_dod/
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