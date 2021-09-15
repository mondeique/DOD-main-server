from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField

# Create your models here.


def icon_thumb_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    return 'dod-explanation/icon/{}'.format(filename)


def link_notice_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    return 'link-notice/{}'.format(filename)


def menu_icon_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    return 'menu_icon/{}'.format(filename)


# class LotteryEndMessage(models.Model):
#     """
#     당첨확인 페이지 안내 멘트
#     """
#     NORMAL_WIN = 1  # 당첨
#     NORMAL_LOSE = 2  # 당첨안됨
#     INACTIVE = 10  # 기프티콘 업로드 안됨
#     ONBOARDING = 20  # 테스트 링크
#     TEST = 30  # 실시간 추첨 체험
#     DOD_WIN = 40  # 디오디 자체 추첨 당첨
#     DOD_LOSE = 41  # 디오디 자체 추첨 꽝
#     KINDS = (
#         (NORMAL_WIN, 'win'),
#         (NORMAL_LOSE, 'lose'),
#         (INACTIVE, 'inactive'),
#         (ONBOARDING, 'onboarding'),
#         (TEST, 'test'),
#         (DOD_WIN, 'dod_win'),
#         (DOD_LOSE, 'dod_lose'),
#     )
#     main_message = models.CharField(max_length=50)
#     sub_message = models.CharField(max_length=50)
#     kind = models.IntegerField(choices=KINDS)
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)


class LinkCopyMessage(models.Model):
    """
    링크 복사 안내 메세지.
    """
    ACTIVE = 1  # 정상적으로 생성
    INACTIVE = 2  # 상품 없이 생성
    ONBOARDING = 3  # 온보딩으로 생성
    KINDS = (
        (ACTIVE, 'active'),
        (INACTIVE, 'inactive'),
        (ONBOARDING, 'test'),
    )
    title = models.CharField(max_length=40)
    kinds = models.IntegerField(choices=KINDS, default=1)
    content = models.TextField(help_text="rich_text_field로 이미지 등을 추가할 수 있습니다.", null=True, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '[10] 링크안내 멘트'


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
    order = models.IntegerField(null=True)
    title = RichTextUploadingField()
    text = RichTextUploadingField()
    icon = models.ImageField(upload_to=icon_thumb_directory_path)
    link_url = models.URLField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '[2] 디오디설명'


class TestGoogleFormsUrl(models.Model):
    forms_url = models.URLField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '[9] 디오디-테스트-구글폼링크'
