import math

from django.conf import settings
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from board.models import Board
from core.permissions import BoardViewPermission
from projects.models import Project
from board.serializers import BoardCreateSerializer, BoardUpdateSerializer, BoardInfoSerializer
from core.pagination import DodPagination
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import time

from respondent.models import Respondent


def _google_info_crawler(form_url):
    try:
        headers = {'User-Agent': 'Chrome/66.0.3359.181'}
        req = Request(form_url, headers=headers)
        html = urlopen(req)
        source = BeautifulSoup(html, 'html.parser')
        temp_str = str(source.find('div'))
        if 'google' in temp_str:
            # docs.google.com 인지 확인
            valid = True
        else:
            valid = False
        dod_html = source.find_all('script', type='text/javascript')
        dod_html_link = dod_html[-1]
        string_html = str(dod_html_link)

        if settings.DEVEL or settings.STAG:
            check_link = 'http://3.36.156.224:8010/checklink'
        else:
            check_link = 'https://d-o-d.io/checklink'

        if check_link in string_html:
            list_html = string_html.split(check_link)
            hash_key = list_html[1].split('/')[1]
            if not len(hash_key) == 12:
                hash_key = hash_key[:12]
        else:
            hash_key = None
        html.close()
    except Exception:
        hash_key = None
        valid = False
    return hash_key, valid


class BoardViewSet(viewsets.ModelViewSet):
    permission_classes = [BoardViewPermission, ]
    queryset = Board.objects.filter(is_active=True).order_by('-id')

    def get_serializer_class(self):
        if self.action == 'create':
            return BoardCreateSerializer
        elif self.action in 'update':
            return BoardUpdateSerializer
        elif self.action in ['retrieve', 'list']:
            return BoardInfoSerializer
        else:
            return super(BoardViewSet, self).get_serializer_class()

    @action(methods=['post'], detail=False)
    def check_dod(self, request, *args, **kwargs):
        """
        api: api/v1/board/check_dod/
        method : POST
        data: {'form_link'}
        return : {'is_dod', 'project'}
        """
        google_form_link = request.data.get('form_link')
        is_dod = False
        project_id = None
        project_hash_key, valid = _google_info_crawler(google_form_link)
        if Project.objects.filter(project_hash_key=project_hash_key).exists():
            is_dod = True
            project_id = Project.objects.get(project_hash_key=project_hash_key).id
        return Response({"valid": valid, "is_dod": is_dod, "project": project_id})

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
        return super(BoardViewSet, self).retrieve(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super(BoardViewSet, self).get_serializer_context()
        context.update({"request": self.request})
        context.update({"user": self.request.user})
        return context


class CumulativeDrawsCountAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        respondents = Respondent.objects.all().count()
        count = 4000 + respondents
        if count >= 1000000:
            value = "%.0f%s" % (count / 1000000.00, 'M+')
        else:
            if count >= 1000:
                value = "{}{}".format(round(count / 1000.0, 1), 'k+')
            else:
                value = count
        return Response({'count': value}, status=status.HTTP_200_OK)
