from django.db import models

# Create your models here.
from projects.models import Project


class UserSelectLogic(models.Model):
    """
    추후 유저가 로직을 선택한다면 사용할 모델입니다.
    선택한 Kinds에 따라 다른 로직 데이터를 저장합니다.
    하나의 프로젝트에 하나의 결과선택이 대응되는게 맞지만, 추후 수정기능을 고려하여 1:N 관계로 설정하였습니다.
    """
    DateTime = 1
    RandomNumber = 2
    KINDS = (
        (DateTime, '시간별'),
        (RandomNumber, '숫자'),
    )
    kind = models.IntegerField(choices=KINDS)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="select_logics")


class DateTimeLotteryResult(models.Model):
    """
    시간으로 추첨하는 로직의 '시간정보'를 저장합니다.
    """
    lucky_time = models.DateTimeField()
    logic = models.ForeignKey(UserSelectLogic, null=True, on_delete=models.SET_NULL, related_name='lottery_times')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_used = models.BooleanField(default=False)