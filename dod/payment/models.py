from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
# Create your models here.
from projects.models import Project


def qrimg_directory_path(instance, filename):
    return 'deposit_without_bankbook/{}/qr/{}'.format(instance.company_name, filename)


class UserDepositLog(models.Model):
    """
    유저의 입금내역입니다.
    스태프는 이 모델을 참고하여 입금확인을 진행합니다.
    프로젝트 생성버튼 클릭시 가격, 프로젝트 등을 저장하고
    다음페이지인 무통장입금 안내 페이지에서 입금자명을 입력시 업데이트합니다.
    * 현재 프로젝트 생성 api 에 엮어있으므로 추후 PG 결제 추가시 삭제필요
    """
    project = models.ForeignKey(Project, null=True, on_delete=models.SET_NULL, related_name='deposit_logs')
    total_price = models.IntegerField(help_text="가격은 서버에서 계산합니다.")
    depositor = models.CharField(max_length=30, null=True, blank=True, help_text="예금주입니다.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirm = models.BooleanField(default=False, help_text="스태프가 계좌 확인 후 True로 변경. True변경시 Project status도 바뀝니다.")

    class Meta:
        verbose_name_plural = '유저 입금내역'


class DepositWithoutBankbook(models.Model):
    """
    무통장 입금 계좌 안내 모델입니다.
    [DEPRECATED]
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
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '입금링크-모바일'


class DepositWithoutBankbookQRimage(models.Model):
    """
    무통장 입금 pc QRcode 모델입니다.
    """
    company_name = models.CharField(max_length=20)
    qr_img = models.ImageField(null=True, upload_to=qrimg_directory_path)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '입금QR코드-PC'


class DepositWithoutBankbookNotice(models.Model):
    """
    무통장입금 안내 멘트 또는 이미지입니다.
    """
    title = models.CharField(max_length=40)
    content = RichTextUploadingField(help_text="rich_text_field로 이미지 등을 추가할 수 있습니다.")
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '안내멘트/이미지'
