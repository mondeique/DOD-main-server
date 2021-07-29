from django.db import models

# Create your models here.

from django.conf import settings
from projects.models import Project


class Board(models.Model):
    form_link = models.URLField(help_text="DOD 가 붙은 설문일수도 있고 아닐수도 있음")
    title = models.CharField(max_length=100)
    content = models.TextField()
    # start_at = models.DateTimeField(null=True, blank=True, help_text="프로젝트 실행일. DOD 없는 경우는 null")
    # dead_at = models.DateTimeField(null=True, blank=True, help_text="프로젝트 마감일. DOD 없는 경우는 null")
    reward_text = models.CharField(null=True, blank=True, max_length=100, help_text="경품 종류 text")
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE, related_name="board")
    is_dod = models.BooleanField(default=False, help_text="DOD 여부")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='boards')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True, help_text='게시물의 유효성을 나타냅니다. True인 애들만 뿌려주기')

