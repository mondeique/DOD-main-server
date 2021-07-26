from django.conf import settings
from rest_framework import serializers
from board.models import Board
from projects.models import Project


class BoardCreateSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Board
        fields = ['form_link', 'title', 'content', 'project', 'owner']

    def create(self, validated_data):

        project_id = validated_data['project']
        if project_id:
            self.project = Project.objects.get(id=project_id)
            validated_data['start_at'] = self.project.start_at
            validated_data['dead_at'] = self.project.dead_at
            # TODO: reward_text 어떻게 채움?? 직접업로드시...
            products_name_list = self.project.products.values_list('item__short_name', flat=True)
            for i in range(len(products_name_list) - 1):
                if products_name_list[i] == products_name_list[i+1]:
                    products_string = products_name_list[i] + ' ' + str(len(products_name_list)) + '개'
                else:
                    products_string = products_name_list[0] + ' 외' + str(len(products_name_list) - 1) + '개'
            validated_data['reward_text'] = products_string
            validated_data['is_dod'] = True
        super(BoardCreateSerializer, self).create(validated_data)


class BoardUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Board
        fields = ['title', 'content']


class BoardListSerializer(serializers.ModelSerializer):
    total_respondent = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ['id', 'title', 'start_at', 'dead_at', 'reward_text', 'total_respondent', 'is_dod']

    def get_total_respondent(self, obj):
        count = obj.project.respondents.all().count()
        return count


class BoardInfoSerializer(serializers.ModelSerializer):
    total_respondent = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ['__all__']

