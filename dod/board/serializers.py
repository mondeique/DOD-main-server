import datetime

from django.conf import settings
from rest_framework import serializers
from board.models import Board
from products.models import Item
from projects.models import Project


class BoardCreateSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Board
        fields = ['form_link', 'title', 'content', 'project', 'owner']

    def create(self, validated_data):

        project = validated_data['project']
        if project:
            self.project = project
            self._set_reward_text()
            validated_data['reward_text'] = self.reward_text
            validated_data['is_dod'] = True
        board = super(BoardCreateSerializer, self).create(validated_data)
        return board

    def _set_reward_text(self):
        if self.project.custom_gifticons.exists():
            count = self.project.custom_gifticons.all().count()
            reward_text = '기프티콘 {}개'.format(count)
        else:
            products = self.project.products.all()
            products_id_list = products.order_by('-item__price').values_list('item', flat=True)
            products_count = products_id_list.count()  # 전체 개수
            products_distinct_count = products_id_list.distinct().count()  # 중복제거 후 개수
            representative_item = Item.objects.get(id=products_id_list[0])
            if products_distinct_count > 1:
                # 여러개 기프티콘: 비싼 상품 + 외 개수
                count = products_count - 1
                reward_text = '{} 외 {}개'.format(representative_item.short_name, count)
            else:
                count = products_count
                reward_text = '{} {}개'.format(representative_item.short_name, count)
        self.reward_text = reward_text


class BoardUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Board
        fields = ['title', 'content']


class BoardInfoSerializer(serializers.ModelSerializer):
    total_respondent = serializers.SerializerMethodField()
    period = serializers.SerializerMethodField()
    project_status = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ['id', 'is_owner', 'form_link', 'title', 'content', 'period', 'reward_text', 'total_respondent', 'is_dod', 'project_status']

    @staticmethod
    def get_period(obj):
        if obj.project:
            start_at = obj.project.start_at
            dead_at = obj.project.dead_at
            period = '{}~{}'.format(start_at.strftime('%m/%d'), dead_at.strftime('%m/%d'))
        else:
            period = None
        return period

    @staticmethod
    def get_total_respondent(obj):
        if obj.project:
            if obj.owner.is_staff:
                count = obj.project.respondents.all().count()
                if count > 50:
                    count = count + 40
            else:
                count = obj.project.respondents.all().count()
        else:
            count = None
        return count

    @staticmethod
    def get_project_status(obj):
        status = 0
        if obj.project:
            start_at = obj.project.start_at
            dead_at = obj.project.dead_at
            now = datetime.datetime.now()
            if now > dead_at or not obj.project.is_active:  # end
                status = -2
            elif now < start_at:  # not started
                status = -1
            else:
                status = 1  # working
        return status

    def get_is_owner(self, obj):
        owner = obj.owner
        user = self.context['user']
        if user == owner:
            return True
        else:
            return False
