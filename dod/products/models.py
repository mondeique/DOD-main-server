import random
import string

from django.db import models

# Create your models here.
from projects.models import Project


def generate_random_key(length):
    return ''.join(random.choices(string.digits+string.ascii_letters, k=length))


def item_thumb_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    return 'product/{}.{}'.format(generate_random_key(7), ext)


def won_thumb_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    return 'product/{}.{}'.format(generate_random_key(7), ext)


def brand_logo_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    return 'product/{}.{}'.format(generate_random_key(7), ext)


def reward_img_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    return 'project/{}/item/{}/{}.{}'.format(
        instance.product.project.project_hash_key,
        instance.product.item.id,
        generate_random_key(5),
        ext)


def custom_gifticon_img_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    return 'project/{}/custom_gifticon/{}/{}.{}'.format(
        instance.project.project_hash_key,
        instance.item.id,
        generate_random_key(5),
        ext)


class Brand(models.Model):
    """
    스타벅스 등 브랜드 목록
    """
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '상품-브랜드'


class Item(models.Model):#TODO : 미리 채워두는 모델
    """
    아이스아메리카노 등 상품 목록
    """
    order = models.IntegerField(unique=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='items')
    thumbnail = models.ImageField(upload_to=item_thumb_directory_path, null=True, blank=True)
    won_thumbnail = models.ImageField(upload_to=won_thumb_directory_path, null=True, help_text='당첨자 페이지에 사용하는 이미지')
    brand_logo = models.ImageField(upload_to=brand_logo_directory_path, null=True, blank=True, help_text='당첨자 페이지에 사용하는 이미지')
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    short_name = models.CharField(max_length=30, null=True, blank=True)
    price = models.IntegerField()
    origin_price = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} {}'.format(self.brand.name, self.name)

    class Meta:
        verbose_name_plural = '상품-아이템'


class Product(models.Model):
    """
    프로젝트 생성시 유저가 선택하는 상품입니다.
    중복선택 가능.
    결제시 해당 모델로 상품을 관리하며, 결제완료시 STATUS가 1로 바뀝니다.
    부분취소 또는 프로젝트 수정시에 이 모델의 STATUS로 기록하며, 추후 Payment 모델에서 결제 금액을 관리합니다.
    """

    STATUS = [
        (0, '결제 전'),
        (1, '상품결제완료'),
        (2, '상품결제취소'),
    ]

    status = models.IntegerField(choices=STATUS, default=0)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='products')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    price = models.IntegerField(help_text='결제금액입니다. 변동될 수 있기 때문에 따로 저장합니다.', default=0)
    count = models.IntegerField(help_text="결제 연동을 하면서 product가 상품단위가 되었습니다. count로 관리하지 않고, 무조건 하나씩 생성합니다.", default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = '결제상품'

    def __str__(self):
        return '[{}]유저 [{}] [{}]상품 [{}]개 생성'.format(
            self.project.owner.phone,
            self.project.name,
            self.item.name,
            self.count
        )


class Reward(models.Model):
    """
    프로덕트에서 유저가 구매한 상품의 정보를 저장하는 모델입니다.
    스태프가 채워야 합니다.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="rewards")
    reward_img = models.ImageField(upload_to=reward_img_directory_path)
    winner_id = models.IntegerField(null=True, blank=True, help_text="당첨자(Respondent)의 id를 저장합니다.")
    due_date = models.CharField(max_length=30, default='')
    # short_name = models.CharField()

    class Meta:
        verbose_name_plural = '유저구매상품-실물'

    def __str__(self):
        return '[{}]상품 중 id_{}'.format(
            self.product.item.name,
            self.id
        )


class CustomGifticon(models.Model):
    """
    유저가 직접 업로드시 사용하는 모델입니다.
    기존과 동일하게 이용하는건 Item의 Thumbnail뿐.
    이 하나의 모델 내에서 당첨자관리(기존 Reward), 직접업로드한 이미지 관리(기존 Reward)를 합니다.
    수정은 구현 x / 삭제는 구현 o (시작 전 일 때)
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='custom_gifticons')
    item = models.ForeignKey(Item, null=True, on_delete=models.SET_NULL, related_name='custom_gifticons', help_text='대표이미지 사용을 위함.')
    gifticon_img = models.ImageField(upload_to=custom_gifticon_img_directory_path)
    winner_id = models.IntegerField(null=True, blank=True, help_text="당첨자(Respondent)의 id를 저장합니다.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
