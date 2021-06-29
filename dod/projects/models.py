from django.db import models

# Create your models here.
from dod import settings


class Project(models.Model):
    name = models.CharField(max_length=30)
    winner_count = models.IntegerField(null=True, help_text="유저가 설정한 당첨자수. UX상 필요. 현재는 이 숫자로 사용/ 추후 차등지급 붙을시는 로직 필요")
    start_at = models.DateTimeField(help_text="프로젝트 실행일. 프로젝트가 시작되는 날짜와 시간을 입력해야합니다.")
    dead_at = models.DateTimeField(help_text="프로젝트 마감일. 중지시 dead_at을 현재시간으로")
    # project_url = models.URLField(help_text="referrer로 유효성 검증. 해당 Url 접속시 핸드폰 인증 화면으로")
    project_hash_key = models.CharField(max_length=100)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects')
    status = models.BooleanField(default=False, help_text="결제하기전에는 False, staff 결제확인시 True : 무통장입금 결제 확인용") #Todo payment 붙으면 나중가서 힘내자

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=False, help_text='프로젝트 유효성을 저장합니다.')

    def __str__(self):
        return '[{}]님의 프로젝트{}'.format(self.owner.phone, self.name)


class ProjectMonitoringLog(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="monitoring_logs")
    draw_again = models.BooleanField(default=False, help_text='모니터링 이후 True, 매번 쿼리하지 않기 위해 사용합니다.')
    dead_line_notice = models.BooleanField(default=False, help_text='프로젝트 마감 알림 이후 True, 매번 쿼리하지 않기 위해 사용합니다.')
