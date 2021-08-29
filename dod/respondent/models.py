import random
import string

from django.db import models

# Create your models here.
from projects.models import Project


class AlertAgreeRespondent(models.Model):
    """
    실시간 추첨 알림 수신 동의한 응답자들 정보
    """
    phone = models.CharField(max_length=20)
    key = models.CharField(max_length=10)
    agree = models.BooleanField(default=False)
    send = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class RespondentPhoneConfirm(models.Model):
    """
    설문자에게만 이용되는 핸드폰인증 모델입니다.
    나중에 파기한다면 이 데이터를 파기해주세요.
    """
    phone = models.CharField(max_length=20)
    confirm_key = models.CharField(max_length=4)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '[{}]님, 인증번호 {} 확인{}'.format(self.phone, self.confirm_key, self.is_confirmed)


class Respondent(models.Model):
    """
    프로젝트당 설문응모자 모델입니다.
    RewardPhoneConfirm 이 is_confirmed = True 시 생성되며, 추후 당첨여부가 저장됩니다.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="respondents")
    phone_confirm = models.OneToOneField(RespondentPhoneConfirm, on_delete=models.CASCADE, related_name='respondent',
                                         help_text="Phone Confirm 이 True 일때만 Reward 생성")
    is_win = models.BooleanField(default=False, help_text="Reward의 winner_id로 사용해도 되지만, 대시보드 쿼리 속도 향상을 위해 사용")


class DeviceMetaInfo(models.Model):
    """
    React 에서 referer가 동작하지 않아, 서버에서 request.META 에서 검증후 redirect 합니다.
    이때, 어뷰징의 위험이 있기 때문에 최대한 request.ip 와 request.META['HTTP_USER_AGENT'] 를 이용하여 유효한 토큰을 발행합니다.
    토근은 referer 통과하면 무조건 발행합니다.

    * 공용 wifi를 사용하면 ip로만은 유효성을 검증할 수 없기 때문에, 같은 ip 와 같은 HTTP_USER_AGENT 로 접속한 경우 토큰이 유효하다 판단합니다.
    * 공용 wifi, 같은 device & 검색엔진(Chrome 등)을 사용할 확률은 적다 판단하여 이렇게 사용합니다.
    ** 어뷰징 케이스
        - referer 변조해서 들어왔을때 : 어차피 중복응모 불가하게 함.
        - referer 변조 후 계속해서 토큰 발행하고, 공용 wifi 및 같은 검색엔진일 경우 : 막을방법 없음.
    """
    ip = models.TextField(max_length=100)
    user_agent = models.TextField()
    validator = models.CharField(max_length=30)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class TestRespondentPhoneConfirm(models.Model):
    """
    메인페이지 테스트 설문자에게만 이용되는 핸드폰인증 모델입니다.
    """
    phone = models.CharField(max_length=20)
    confirm_key = models.CharField(max_length=4)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '테스트) [{}]님, 인증번호 {} 확인{}'.format(self.phone, self.confirm_key, self.is_confirmed)


class TestRespondent(models.Model):
    """
    테스트 프로젝트당 설문응모자 모델입니다.
    RewardPhoneConfirm 이 is_confirmed = True 시 생성되며, 항상 당첨.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="test_respondents")
    phone_confirm = models.OneToOneField(TestRespondentPhoneConfirm, on_delete=models.CASCADE, related_name='test_respondent',
                                         help_text="Phone Confirm 이 True 일때만 Reward 생성")
    is_win = models.BooleanField(default=True, help_text="Reward의 winner_id로 사용해도 되지만, 대시보드 쿼리 속도 향상을 위해 사용")
