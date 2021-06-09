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
        fields = ['owner', 'winner_count', 'created_at', 'dead_at']

    def create(self, validated_data):
        validated_data['project_hash_key'] = generate_hash_key()
        validated_data['name'] = generate_project_name()
        project = super(ProjectCreateSerializer, self).create(validated_data)
        return project


class ProjectUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = ['name', 'created_at', 'dead_at']


class ProjectDepositInfoRetrieveSerializer(serializers.ModelSerializer):
    """
    프로젝트 생성버튼클릭시 리턴하는 데이터입니다.
    해당 데이터를 사용하여 무통장입금 안내시 가격, 프로젝트 기본정보를 제공합니다.

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
    dead_at = serializers.SerializerMethodField()
    is_done = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'total_respondent', 'products', 'dead_at', 'is_done', 'status']

    def get_total_respondent(self, obj):
        count = obj.respondents.all().count()
        return count

    def get_products(self, obj):
        products = obj.products.all()
        serializer = ProductSimpleDashboardSerializer(products, many=True)
        return serializer.data

    def get_dead_at(self, obj):  # humanize
        return obj.dead_at.strftime("%Y년 %m월 %d일까지")

    def get_is_done(self, obj):
        now = datetime.datetime.now()
        if obj.dead_at < now:
            return True
        else:
            return False


class SimpleProjectInfoSerializer(serializers.ModelSerializer):
    dead_at = serializers.SerializerMethodField()
    is_started = serializers.SerializerMethodField()
    is_done = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'dead_at', 'is_started', 'is_done', 'status']

    def get_dead_at(self, obj):  # humanize
        return obj.dead_at.strftime("%Y년 %m월 %d일까지")

    def get_is_started(self, obj):
        now = datetime.datetime.now()
        if obj.start_at < now:
            return True
        else:
            return False

    def get_is_done(self, obj):
        now = datetime.datetime.now()
        if obj.dead_at < now:
            return True
        else:
            return False


class ProjectLinkSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    link_notice = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['url', 'link_notice']

    def get_url(self, obj):
        hash_key = obj.project_hash_key
        # url = 'https://d-o-d.io/link/{}'.format(hash_key)
        url = 'http://3.36.156.224:8000/link/{}'.format(hash_key)
        return url

    def get_link_notice(self, obj):
        link_notice = LinkCopyNotice.objects.filter(is_active=True).last()
        serializer = LinkNoticeSerializer(link_notice)
        return serializer.data
