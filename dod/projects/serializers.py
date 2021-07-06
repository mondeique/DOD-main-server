from django.conf import settings
from rest_framework import serializers
import random
import string
import datetime

from notice.models import LinkCopyNotice
from notice.serializers import LinkNoticeSerializer
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
        fixed_start_at = start_at + datetime.timedelta(hours=9, minutes=1)
        dead_at = validated_data['dead_at']
        fixed_dead_at = dead_at + datetime.timedelta(days=1, hours=8, minutes=59, seconds=59)
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
        fixed_start_at = start_at + datetime.timedelta(hours=9)
        dead_at = validated_data['dead_at']
        fixed_dead_at = dead_at + datetime.timedelta(days=1, hours=8, minutes=59, seconds=59)
        validated_data['start_at'] = fixed_start_at
        validated_data['dead_at'] = fixed_dead_at
        project = super(ProjectUpdateSerializer, self).update(instance, validated_data)
        return project


class ProjectDepositInfoRetrieveSerializer(serializers.ModelSerializer):
    """
    프로젝트 생성버튼클릭시 리턴하는 데이터입니다.
    해당 데이터를 사용하여 무통장입금 안내시 가격, 프로젝트 기본정보, 입금 안내링크를 제공합니다.

    * project id를 가지고 입금확인 버튼을 요청해야 입금자명을 저장할 수 있습니다.
    """

    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'winner_count', 'total_price']

    def get_total_price(self, obj):
        products = obj.products.all()
        total_price = 0
        for product in products:
            item_price = product.item.price
            price = item_price * product.count
            total_price = total_price + price
        return total_price


class ProjectDashboardSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    total_respondent = serializers.SerializerMethodField()
    start_at = serializers.SerializerMethodField()
    dead_at = serializers.SerializerMethodField()
    project_status = serializers.SerializerMethodField()
    depositor = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'total_respondent',
                  'products', 'start_at', 'dead_at',
                  'project_status', 'depositor', 'total_price']

    def get_total_respondent(self, obj):
        count = obj.respondents.all().count()
        return count

    def get_products(self, obj):
        data = []
        products = obj.products.all()
        item_id_list = list(products.values_list('item_id', flat=True).distinct())
        for item in item_id_list:
            dic = {}
            products_qs = products.filter(item__id=item)
            thumbnail = products_qs.last().item.thumbnail.url
            winner_count = products_qs.count()
            remain_winner_count = products_qs.filter(rewards__winner_id__isnull=True).count()
            dic['item_thumbnail'] = thumbnail
            dic['remain_winner_count'] = remain_winner_count
            dic['winner_count'] = winner_count
            data.append(dic)
        return data

    def get_start_at(self, obj):  # humanize
        return obj.start_at.strftime("%m월 %d일")

    def get_dead_at(self, obj):  # humanize
        return obj.dead_at.strftime("%m월 %d일")

    def get_project_status(self, obj):
        now = datetime.datetime.now()
        if obj.dead_at < now:
            return 999  # 종료됨
        elif not obj.status:
            return 200  # 입금대기중
        elif obj.start_at > now:
            return 300  # 프로젝트 대기중
        else:
            return 100  # 진행중F

    def get_depositor(self, obj):
        if obj.deposit_logs.exists():
            return obj.deposit_logs.last().depositor
        else:
            return None

    def get_total_price(self, obj):
        if obj.deposit_logs.exists():
            return obj.deposit_logs.last().total_price
        else:
            return 0


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
            url = 'https://docs.gift/link/{}/'.format(hash_key)
        else:
            url = 'https://dod-link.com/{}/'.format(hash_key) # TODO : link api 수정
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


