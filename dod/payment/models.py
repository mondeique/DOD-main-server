from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
# Create your models here.


def qrimg_directory_path(instance, filename):
    return 'deposit_without_bankbook/{}/qr/{}'.format(instance.company_name, filename)


class DepositWithoutBankbook(models.Model):
    """
    무통장 입금 계좌 모델입니다.
    """
    account = models.CharField(max_length=50)
    holder = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DepositWithoutBankbookShortCutLink(models.Model):
    """
    무통장 입금 모바일 링크 모델입니다.
    """
    company_name = models.CharField(max_length=20)
    link = models.URLField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DepositWithoutBankbookQRimage(models.Model):
    """
    무통장 입금 pc QRcode 모델입니다.
    """
    company_name = models.CharField(max_length=20)
    qr_img = models.ImageField(null=True, upload_to=qrimg_directory_path)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DepositWithoutBankbookNotice(models.Model):
    """
    무통장입금 안내 멘트 또는 이미지입니다.
    """
    title = models.CharField(max_length=40)
    content = RichTextUploadingField(help_text="rich_text_field로 이미지 등을 추가할 수 있습니다.")
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
