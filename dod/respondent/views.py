from django.conf import settings
from django.http import HttpResponseRedirect
import random
import string
import datetime

from django.shortcuts import render
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


# Create your views here.
from core.slack import staff_reward_didnt_upload_slack_message
from core.tools import get_client_ip
from projects.models import Project
from respondent.models import DeviceMetaInfo
from respondent.serializers import ClientRefererProjectValidateSerializer


class RefererValidatorAPIView(APIView):
    permission_classes = [AllowAny]

    def __init__(self):
        super(RefererValidatorAPIView, self).__init__()
        self.project = None

    def get(self, request, *args, **kwargs):
        """
        유저가 구글폼 마지막에 붙여넣는 url 입니다.

        접속시,
            1. referer를 체크하고
            2. project의 유효성을 검증하고
            3. 1,2를 통과하면 DeviceMetaInfo 생성 후 client 핸드폰 인증 페이지로 redirect 시킵니다.
            * client 는 핸드폰 인증 페이지 접속시 project와 validator가 유효한지 확인하는 api로 체크 후 렌더링 시켜야 합니다.
            => 외부접속 막기 위함.

        api : d-o-d.io/link/<slug>
        return : None,
        redirect : client_ip/<confirm_page>/?val=~~&?p=~~/
        """
        # base_url = 'https://d-o-d.io/'
        # base_url = 'http://3.37.147.189:8000'/
        # base_url = 'http://172.30.1.26:3000/'

        if settings.DEVEL or settings.STAG:
            base_url = 'http://172.30.1.26:3000/'
        else:
            base_url = 'https://dod-beta.com/'

        self.referer = request.META.get('HTTP_REFERER', "")

        if not self._check_referer():
            # client forbidden page
            # TODO: client url
            forbidden_url = base_url + 'forbidden'
            return HttpResponseRedirect(forbidden_url)

        project_hash_key = kwargs['slug']
        self.project = Project.objects.filter(project_hash_key=project_hash_key).last()

        if not self.project or not self._validate_project():
            # project not started page
            project_not_start_url = base_url + 'invalid'
            return HttpResponseRedirect(project_not_start_url)

        if self.project.products.filter(rewards__isnull=True).exists():
            msg = '[기프티콘 업로드 안됨]\n검색 키: {}\n시작 일: {}\n활성화 여부: {}'\
                .format(self.project.project_hash_key,
                        self.project.start_at,
                        self.project.is_active)
            staff_reward_didnt_upload_slack_message(msg)
            project_not_start_url = base_url + 'invalid'
            return HttpResponseRedirect(project_not_start_url)

        ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', "")  # TODO: if user_agent is null
        validator = self._generate_validator()
        DeviceMetaInfo.objects.create(ip=ip,
                                      user_agent=user_agent,
                                      validator=validator)

        # client phone confirm(Success) page with query: project, validator
        # TODO: client url
        respondent_phone_register_url = base_url + 'link?p={}&v={}'.format(project_hash_key, validator)
        return HttpResponseRedirect(respondent_phone_register_url)

    def _check_referer(self):
        if "google.com" in self.referer:
            return True
        else:
            return False

    def _validate_project(self):
        now = datetime.datetime.now()
        if self.project.dead_at < now:
            return False  # 종료됨
        elif not self.project.status:
            return False  # 입금대기중
        elif not self.project.is_active:
            return False  # 프로젝트 삭제됨(환불시)
        elif self.project.start_at > now:
            return False  # 프로젝트 대기중
        else:
            return True  # 진행중

    def _generate_validator(self):
        return ''.join(random.choices(string.digits + string.ascii_letters, k=20))


class ClientRefererProjectValidateCheckViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    queryset = DeviceMetaInfo.objects.all()
    serializer_class = ClientRefererProjectValidateSerializer

    @action(methods=['post'], detail=False)
    def is_valid(self, request, *args, **kwargs):
        """
        client 핸드폰 인증 페이지 접속시, 유효한 접근인지 체크하는 api 입니다.

        api : d-o-d.io/api/v1/check/is_valid
        body : {'project_key', 'validator'}
        return : 100: pass, 400: project is not valid, 999: validator is not valid
        """
        data = request.data
        serializer = self.get_serializer(data=data)
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            validator = self.get_queryset().filter(validator=data.get('validator'))
            if not validator.exists():
                return Response(status=status.HTTP_404_NOT_FOUND)
            validator = validator.last()
            ip = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', "")
            if validator.ip != ip or validator.user_agent != user_agent or validator.is_confirmed:
                return Response({'dod_status': 999}, status=status.HTTP_200_OK)

            self.project = Project.objects.filter(project_hash_key=data.get('project_key')).last()
            if not self.project or not self._validate_project():
                return Response({'dod_status': 400}, status=status.HTTP_200_OK)

        return Response({'dod_status': 100}, status=status.HTTP_200_OK)

    def _validate_project(self):
        now = datetime.datetime.now()
        if self.project.dead_at < now:
            return False  # 종료됨
        elif not self.project.status:
            return False  # 입금대기중
        elif not self.project.is_active:
            return False  # 프로젝트 삭제됨(환불시)
        elif self.project.start_at > now:
            return False  # 프로젝트 대기중
        else:
            return True  # 진행중


def home(request, **kwargs):
    ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', "")
    referer = request.META.get('HTTP_REFERER', "")
    d = request.META
    context = {'ip': ip, 'agent': user_agent, 'referer': referer, 'data':d}

    return render(request, 'test.html', context)
