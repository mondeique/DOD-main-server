from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField

# Create your models here.


def icon_thumb_directory_path(instance, filename):
    return 'dod-explanation/icon/{}'.format(filename)


class LinkCopyNotice(models.Model):
    """
    메인 대시보드에서 링크 복사 클릭시 나오는 안내 페이지입니다.
    """
    title = models.CharField(max_length=40)
    content = RichTextUploadingField(help_text="rich_text_field로 이미지 등을 추가할 수 있습니다.")
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '링크복사 안내'


class NoticeLink(models.Model):
    """
    공지사항 노션 링크입니다.
    """
    link = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '공지사항-노션링크'


class FAQLink(models.Model):
    """
    자주묻는 질문 노션 링크입니다.
    """
    link = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '자주묻는질문-노션링크'


class ContactLink(models.Model):
    """
    문의하기 링크입니다.
    """
    link = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '문의하기-링크'


class SuggestionLink(models.Model):
    """
    건의하기 링크입니다.
    """
    link = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '건의하기-링크'


class MainPageDodExplanation(models.Model):
    title = RichTextUploadingField()
    text = RichTextUploadingField()
    icon = models.ImageField(upload_to=icon_thumb_directory_path)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '디오디설명'
