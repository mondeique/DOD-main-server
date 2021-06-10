from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
import datetime
# Create your views here.
from accounts.models import PhoneConfirm
from accounts.serializers import SMSSignupPhoneCheckSerializer, SMSSignupPhoneConfirmSerializer
from core.sms.utils import SMSV2Manager
from projects.models import Project
from respondent.models import RespondentPhoneConfirm
from respondent.serializers import SMSRespondentPhoneCheckSerializer, RespondentCreateSerializer


class SMSViewSet(viewsets.GenericViewSet):
    """
    sms 전송시 공통으로 사용하는 viewset
    """
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'send':
            serializer = SMSSignupPhoneCheckSerializer
        elif self.action == 'confirm':
            serializer = SMSSignupPhoneConfirmSerializer
        elif self.action == 'respondent_send':
            serializer = SMSRespondentPhoneCheckSerializer
        elif self.action == 'respondent_confirm':
            serializer = None
        else:
            serializer = super(SMSViewSet, self).get_serializer_class()
        return serializer

    @action(methods=['post'], detail=False)
    def send(self, request, *args, **kwargs):
        """
        회원가입시 인증번호 발송하는 api입니다.
        api: api/v1/sms/send
        method: POST
        data: {'phone'}
        """
        data = request.data
        serializer = self.get_serializer(data=data)
        if serializer.is_valid(raise_exception=True):
            phone = serializer.validated_data['phone']
            sms_manager = SMSV2Manager()
            sms_manager.set_content()
            sms_manager.create_instance(phone=phone, kinds=PhoneConfirm.SIGN_UP)

            if not sms_manager.send_sms(phone=phone):
                return Response("Failed send sms", status=status.HTTP_410_GONE)

            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=False)
    def confirm(self, request, *args, **kwargs):
        """
        회원가입시 인증번호 인증 api입니다. 인증시 다음페이지(비밀번호설정)에서 사용할 phone을 리턴합니다.
        api: api/v1/sms/confirm
        method: POST
        data: {'phone', 'confirm_key'}
        """
        data = request.data
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid(raise_exception=True):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response({'phone': serializer.validated_data['phone']}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def respondent_send(self, request, *args, **kwargs):
        """
        설문자 인증번호 발송시 사용하는 핸드폰인증입니다.
        api: api/v1/sms/respondent_send/
        method: POST
        data: {'phone'}
        """
        data = request.data
        serializer = self.get_serializer(data=data)
        if serializer.is_valid(raise_exception=True):
            phone = serializer.validated_data['phone']
            sms_manager = SMSV2Manager()
            sms_manager.set_respondent_content()
            sms_manager.create_respondent_send_instance(phone=phone)

            if not sms_manager.send_sms(phone=phone):
                return Response("Failed send sms", status=status.HTTP_410_GONE)

            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=False)
    def respondent_confirm(self, request, *args, **kwargs):
        """
        설문자  인증번호 인증 api입니다. 인증시 서버에서 5-10초후 reward MMS를 발송합니다.
        api: api/v1/sms/respondent_confirm
        method: POST
        전화번호, 인증번호 와 url에서 파싱한 project_key를 담아서 보내주어야 합니다.
        data: {'phone', 'confirm_key', 'project_key'}
        """
        data = request.data
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid(raise_exception=True):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if not Project.objects.filter(project_hash_key=data.get('project_key')).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        self.data = serializer.validated_data
        self._create_respondent()
        # 여기까지가 유저 당첨확인 및 생성
        # TODO : 문자보내고 로직상 문제있는지 확인
        # TODO : MMS 만들기 및 문자 포맷 admin에서 수정할 수 있게 만들기
        # TODO : MMS 보내고, 쿠폰 안겹치게 Reward winner_id 넣기, 중복안되게 문자발송 쿠폰 체크

        return Response({'phone': serializer.validated_data['phone']}, status=status.HTTP_200_OK)

    def _create_respondent(self):
        self.project = Project.objects.get(project_hash_key=self.data.get('project_key'))
        self.phone_confirm = RespondentPhoneConfirm.objects.filter(phone=self.data.get('phone'),
                                                                   confirm_key=self.data.get('confirm_key'),
                                                                   is_confirmed=True).first()
        self.is_win = self._am_i_winner()
        data = {'project': self.project.id,
                'phone_confirm': self.phone_confirm.id,
                'is_win': self.is_win}

        serializer = RespondentCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def _am_i_winner(self):
        self.lucky_times = self.project.select_logics.last().lottery_times.filter(is_used=False)
        now = datetime.datetime.now()
        self.valid_lucky_times = self.lucky_times.filter(lucky_time__lte=now)
        if not self.valid_lucky_times.exists():
            # 당첨 안된 경우
            return False
        else:
            lucky_time = self.valid_lucky_times.first()
            lucky_time.is_used = True
            lucky_time.save()
            return True


class MMSViewSet(viewsets.GenericViewSet):
    pass
