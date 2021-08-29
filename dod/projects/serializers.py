from django.conf import settings
from rest_framework import serializers
import random
import string
import datetime

from notice.models import LinkCopyNotice
from notice.serializers import LinkNoticeSerializer
from products.models import Product, CustomGifticon
from products.serializers import ProductSimpleDashboardSerializer
from projects.models import Project


def generate_hash_key(length=12):
    return ''.join(random.choices(string.digits+string.ascii_letters, k=length))


def generate_project_name():
    return 'dod설문추첨_' + ''.join(random.choices(string.digits+string.ascii_letters, k=5))


class ProjectCreateSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Project
        fields = ['owner', 'start_at', 'dead_at']

    def create(self, validated_data):
        start_at = validated_data['start_at']
        fixed_start_at = start_at + datetime.timedelta(minutes=1)
        dead_at = validated_data['dead_at']
        fixed_dead_at = dead_at + datetime.timedelta(hours=23, minutes=59, seconds=59)
        validated_data['start_at'] = fixed_start_at
        validated_data['dead_at'] = fixed_dead_at
        validated_data['project_hash_key'] = generate_hash_key()
        validated_data['name'] = self.set_project_name()
        project = super(ProjectCreateSerializer, self).create(validated_data)
        return project

    def set_project_name(self):
        user = self.context['user']
        project_counts = user.projects.count() + 1
        name = '추첨_{}'.format(project_counts)
        return name


class ProjectUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = ['start_at', 'dead_at']

    def update(self, instance, validated_data):
        start_at = validated_data['start_at']
        fixed_start_at = start_at + datetime.timedelta(minutes=1)
        dead_at = validated_data['dead_at']
        fixed_dead_at = dead_at + datetime.timedelta(hours=23, minutes=59, seconds=59)
        validated_data['start_at'] = fixed_start_at
        validated_data['dead_at'] = fixed_dead_at
        project = super(ProjectUpdateSerializer, self).update(instance, validated_data)
        return project


class ProjectDepositInfoRetrieveSerializer(serializers.ModelSerializer):
    """
    프로젝트 생성버튼클릭시 리턴하는 데이터입니다.
    """

    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'winner_count', 'total_price']

    def get_total_price(self, obj):
        if obj.custom_gifticons.exists():
            return 0
        products = obj.products.all()
        total_price = 0
        for product in products:
            item_price = product.item.price
            price = item_price * product.count
            total_price = total_price + price
        return total_price


class ProjectDashboardSerializer(serializers.ModelSerializer):
    total_respondent = serializers.SerializerMethodField()
    start_at = serializers.SerializerMethodField()
    dead_at = serializers.SerializerMethodField()
    project_status = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'total_respondent',
                  'start_at', 'dead_at',
                  'project_status', 'progress']

    def get_total_respondent(self, obj):
        count = obj.respondents.all().count()
        return count

    def get_start_at(self, obj):  # humanize
        return obj.start_at.strftime("%m월 %d일")

    def get_dead_at(self, obj):  # humanize
        return obj.dead_at.strftime("%m월 %d일")

    def get_project_status(self, obj):
        now = datetime.datetime.now()
        if obj.dead_at < now:
            return 999  # 종료됨
        elif not obj.status:
            return 200  # 활성화 안됨 # UPDATED 20210829 onboarding
        elif obj.start_at > now:
            return 300  # 프로젝트 대기중
        else:
            return 100  # 진행중

    def get_progress(self, obj):  # humanize
        project = obj
        if not project.status:
            return 0
        if project.custom_gifticons.exists():
            total_count = project.custom_gifticons.all().count()
            used_count = project.custom_gifticons.filter(winner_id__isnull=False).count()
        else:
            project_qs = project.products.all().prefetch_related('rewards', 'rewards__winner_id')
            total_count = project_qs.count()
            used_count = project_qs.filter(rewards__winner_id__isnull=False).count()
        if total_count == 0:
            total_count = 1
        progress = int(round(used_count / total_count, 2) * 100)
        if progress > 100:
            progress = 100
        return progress


class SimpleProjectInfoSerializer(serializers.ModelSerializer):
    project_status = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'project_status']

    def get_project_status(self, obj):  # humanize #TODO: request validator check
        now = datetime.datetime.now()
        if obj.dead_at < now:
            return False  # 종료됨
        elif not obj.status:
            return False  # 입금대기중
        elif obj.start_at > now:
            return False  # 프로젝트 대기중
        else:
            return True  # 진행중


class ProjectLinkSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    pc_url = serializers.SerializerMethodField()
    mobile_url = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['url', 'pc_url', 'mobile_url']

    def get_url(self, obj): # TODO : respondent validator view api
        hash_key = obj.project_hash_key
        # url = 'https://d-o-d.io/link/{}/'.format(hash_key)
        # url = 'http://3.37.147.189:8000/link/{}/'.format(hash_key)
        if settings.DEVEL or settings.STAG:
            url = 'http://3.36.156.224:8010/checklink/{}'.format(hash_key)  # 2021.07.07 [d-o-d.io 리뉴얼 ]추가 ####
        else:
            url = 'https://d-o-d.io/checklink/{}/'.format(hash_key)
        return url

    def get_pc_url(self, obj):
        link_notice = LinkCopyNotice.objects.filter(is_active=True, kinds=1).last()
        if link_notice.image:
            return link_notice.image.url
        return None

    def get_mobile_url(self, obj):
        link_notice = LinkCopyNotice.objects.filter(is_active=True, kinds=2).last()
        if link_notice.image:
            return link_notice.image.url
        return None


class PastProjectSerializer(serializers.ModelSerializer):
    """
    마이페이지 또는 메뉴에서 지난프로젝트 데이터를 보내주는 serializer 입니다.
    """
    start_at = serializers.SerializerMethodField()
    dead_at = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    total_respondent = serializers.SerializerMethodField()
    end_winner_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'total_respondent',
                  'winner_count', 'start_at', 'dead_at',
                  'total_price', 'end_winner_count']

    def get_total_respondent(self, obj):
        count = obj.respondents.all().count()
        return count

    def get_start_at(self, obj):
        return obj.start_at.strftime("%Y년 %m월 %d일")

    def get_dead_at(self, obj):  # humanize
        return obj.dead_at.strftime("%Y년 %m월 %d일")

    def get_total_price(self, obj):
        products = obj.products.all()
        total_price = 0
        for product in products:
            item_price = product.item.price
            price = item_price * product.count
            total_price = total_price + price
        return total_price

    def get_end_winner_count(self, obj):
        return obj.respondents.filter(is_win=True).count()


class ProjectGifticonSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'data', 'type']

    def project_type(self):
        if self.obj.products.exists():
            return 1
        elif self.obj.custom_gifticons.exists():
            return 2
        else:
            return 0

    def get_type(self, obj):
        self.obj = obj
        return self.project_type()

    def get_data(self, obj):
        self.obj = obj
        project_type = self.project_type()
        if project_type == 1:  # pay
            products_distinct_ids = self.obj.products.all().values_list('item__id', flat=True).distinct()
            distinct_products = self.obj.products.filter(item__id__in=products_distinct_ids)
            empty_dict = {}
            for product in distinct_products:
                empty_dict[product.item.id] = product
            serializer = ProjectProductsGifticonsDetailSerializer(empty_dict.values(), many=True, context={'project': self.obj})
        else:  # custom upload
            custom_gifticons = self.obj.custom_gifticons.all()
            serializer = ProjectCustomGifticonsDetailSerializer(custom_gifticons, many=True)

        return serializer.data


class ProjectProductsGifticonsDetailSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    total_count = serializers.SerializerMethodField()
    left_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'thumbnail', 'total_count', 'left_count']

    def get_thumbnail(self, obj):
        return obj.item.thumbnail.url

    def get_total_count(self, obj):
        project = self.context['project']
        return project.products.filter(item__id=obj.item.id).count()

    def get_left_count(self, obj):
        project = self.context['project']
        return project.products.filter(item__id=obj.item.id, rewards__winner_id__isnull=True).count()


class ProjectCustomGifticonsDetailSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    is_used = serializers.SerializerMethodField()

    class Meta:
        model = CustomGifticon
        fields = ['id', 'thumbnail', 'is_used']

    def get_thumbnail(self, obj):
        return obj.gifticon_img.url

    def get_is_used(self, obj):
        if obj.winner_id:
            return True
        else:
            return False
