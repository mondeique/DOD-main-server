from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField

# Create your models here.


def icon_thumb_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    return 'dod-explanation/icon/{}.{}'.format(filename, ext)


def link_notice_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    return 'link-notice/{}.{}'.format(filename, ext)


def menu_icon_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    return 'menu_icon/{}.{}'.format(filename, ext)


class LinkCopyNotice(models.Model):
    """
    메인 대시보드에서 링크 복사 클릭시 나오는 안내 페이지입니다.
    """
    DESKTOP = 1
    MOBILE = 2
    KINDS = (
        (DESKTOP, 'desktop'),
        (MOBILE, 'mobile'),
    )
    title = models.CharField(max_length=40)
    kinds = models.IntegerField(choices=KINDS, default=1)
    content = RichTextUploadingField(help_text="rich_text_field로 이미지 등을 추가할 수 있습니다.", null=True, blank=True)
    image = models.ImageField(upload_to=link_notice_directory_path, null=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '[1] 링크복사 안내'


class NoticeLink(models.Model):
    """
    공지사항 노션 링크입니다.
    """
    link = models.URLField()
    icon = models.ImageField(null=True, upload_to=menu_icon_directory_path)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '[4] 공지사항-링크'


class FAQLink(models.Model):
    """
    자주묻는 질문 노션 링크입니다.
    """
    link = models.URLField()
    icon = models.ImageField(null=True, upload_to=menu_icon_directory_path)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '[3] 자주묻는질문-링크'


class ContactLink(models.Model):
    """
    문의하기 링크입니다.
    """
    link = models.URLField()
    icon = models.ImageField(null=True, upload_to=menu_icon_directory_path)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '[6] 문의하기-링크'


class SuggestionLink(models.Model):
    """
    건의하기 링크입니다.
    """
    link = models.URLField()
    icon = models.ImageField(null=True, upload_to=menu_icon_directory_path)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '[5] 건의하기-링크'


class PrivacyPolicyLink(models.Model):
    """
    개인정보 처리방침 링크입니다.
    """
    link = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '[7] 개인정보처리방침-링크'


class TermsOfServiceLink(models.Model):
    """
    이용약관 링크입니다.
    """
    link = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '[8] 이용약관-링크'


class MainPageDodExplanation(models.Model):
    title = RichTextUploadingField()
    text = RichTextUploadingField()
    icon = models.ImageField(upload_to=icon_thumb_directory_path)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '[2] 디오디설명'
