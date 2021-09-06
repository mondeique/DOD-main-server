from django.db import models

# Create your models here.
from django.conf import settings

from custom_manage.utils import generate_random_key
from projects.models import Project


def icon_thumb_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    return 'dod-extra-gifticons/icon/{}.{}'.format(filename, ext)

def dod_extra_reward_img_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    return 'project/{}/item/{}/{}.{}'.format(
        instance.project.project_hash_key,
        instance.item.id,
        generate_random_key(5),
        ext)


class DODExtraGifticonsItem(models.Model):
    name = models.CharField(max_length=30)
    percentage = models.FloatField()
    price = models.IntegerField()
    thumbnail = models.ImageField(upload_to=icon_thumb_directory_path)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '디오디 자체추첨 상품'


class DODExtraLotteryLogs(models.Model):
    item = models.ForeignKey(DODExtraGifticonsItem, null=True, on_delete=models.SET_NULL,
                             related_name='logs')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, help_text='추첨 프로젝트 정보')
    phone = models.CharField(max_length=20)
    gifticon = models.ImageField(upload_to=dod_extra_reward_img_directory_path,
                                 null=True, blank=True, help_text='디오디 자체추첨 상품')
    due_date = models.CharField(max_length=30, default='')
    send = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '디오디 자체추첨 상품 발송 로그'
