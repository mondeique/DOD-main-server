from rest_framework import serializers
import random
import string
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


class ProjectDepositInfoRetrieveSerializer(serializers.ModelSerializer):
    """
    프로젝트 생성버튼클릭시 리턴하는 데이터입니다.
    해당 데이터를 사용하여 무통장입금 안내시 가격, 프로젝트 기본정보를 제공합니다. TODO: 과연 어떤 정보를 제공할지?

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
