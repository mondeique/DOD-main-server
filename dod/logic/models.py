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
    Percentage = 3
    KINDS = (
        (DateTime, '시간별'),
        (RandomNumber, '숫자'),
        (Percentage, '확률'),
    )
    kind = models.IntegerField(choices=KINDS)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="select_logics")


class DateTimeLotteryResult(models.Model):
    """
    시간으로 추첨하는 로직의 '시간정보'를 저장합니다.
    """
    lucky_time = models.DateTimeField()
    logic = models.ForeignKey(UserSelectLogic, null=True, on_delete=models.CASCADE, related_name='lottery_times')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_used = models.BooleanField(default=False)


class PercentageResult(models.Model):
    """
    확률로 추첨하는 로직의 '확률정보'를 저장합니다.
    """
    percentage = models.FloatField(help_text='당첨확률')
    logic = models.ForeignKey(UserSelectLogic, null=True, on_delete=models.CASCADE, related_name='percentages')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_used = models.BooleanField(default=False)


class DODAveragePercentage(models.Model):
    """
    dod 평균 당첨확률
    """
    average_percentage = models.FloatField(help_text='dod 평균 당첨 확률: 퍼센트 소수점으로 작성')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '디오디 평균 당첨 확률'


class DODExtraAveragePercentage(models.Model):
    """
    추첨 종료 후 디오디 추첨의 진입확률
    """
    extra_average_percentage = models.FloatField(help_text='dod추첨 진입 확률: 퍼센트 소수점으로 작성')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '디오디 자체 추첨 진입 확률'
