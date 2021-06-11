from django.db import models

# Create your models here.
from projects.models import Project


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
    phone_confirm = models.OneToOneField(RespondentPhoneConfirm, on_delete=models.CASCADE, help_text="Phone Confirm 이 True 일때만 Reward 생성")
    is_win = models.BooleanField(default=False, help_text="Reward의 winner_id로 사용해도 되지만, 대시보드 쿼리 속도 향상을 위해 사용")








