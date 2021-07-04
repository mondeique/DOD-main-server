from django.conf import settings
from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
# Create your models here.
from projects.models import Project


def qrimg_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    return 'deposit_without_bankbook/{}/qr/{}'.format(instance.company_name, filename)


class Payment(models.Model):
    """
    결제시 생성되는 모델입니다.
    여러개의 상품을 한번에 결제하면 하나의 Payment obj 가 생성됩니다.
    """
    STATUS = [
        (0, '결제대기'),
        (1, '결제완료'),
        (2, '결제승인전'),
        (3, '결제승인중'),
        (20, '결제취소'),
        (21, '부분결제취소'),
        (-20, '결제취소실패'),
        (-30, '결제취소진행중'),
        (-1, '오류로 인한 결제실패'),
        (-2, '결제승인실패'),
        (999, '서버오류발생.'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='유저')
    receipt_id = models.CharField(max_length=100, verbose_name='영수증키', db_index=True)
    status = models.IntegerField(choices=STATUS, verbose_name='결제상태', default=0)
    project = models.OneToOneField(Project, null=True, on_delete=models.SET_NULL)
    price = models.IntegerField(verbose_name='결제금액', null=True)
    name = models.CharField(max_length=100, verbose_name='대표상품명')

    # bootpay data
    tax_free = models.IntegerField(verbose_name='면세금액', null=True)
    remain_price = models.IntegerField(verbose_name='남은금액', null=True)
    remain_tax_free = models.IntegerField(verbose_name='남은면세금액', null=True)
    cancelled_price = models.IntegerField(verbose_name='취소금액', null=True)
    cancelled_tax_free = models.IntegerField(verbose_name='취소면세금액', null=True)
    pg = models.TextField(default='payapp', verbose_name='pg사')
    method = models.TextField(verbose_name='결제수단')
    payment_data = models.TextField(verbose_name='raw데이터')
    requested_at = models.DateTimeField(blank=True, null=True)
    purchased_at = models.DateTimeField(blank=True, null=True)
    revoked_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return


class PaymentErrorLog(models.Model):
    """
    부트페이에선 결제가 되었지만, done api 호출 시 에러가 나, 서버상에선 결제 완료 처리가 되지 않았을 경우 환불 or 결제 완료
    처리해야 하기 때문에 로그 생성
    """

    # TODO : statelessful 하지 않도록 server side 렌더링이 필요
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    temp_payment = models.ForeignKey(Payment, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.CharField(max_length=100)
    bootpay_receipt_id = models.TextField(null=True, blank=True)
    is_refunded = models.BooleanField(default=False)


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

    def save(self, *args, **kwargs):
        super(UserDepositLog, self).save(*args, **kwargs)
        if self.confirm:
            project = self.project
            project.status = True
            project.save()


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
