from rest_framework import serializers

from notice.models import LinkCopyNotice, MainPageDodExplanation


class LinkNoticeSerializer(serializers.ModelSerializer):

    class Meta:
        model = LinkCopyNotice
        fields = ['id', 'title', 'content']


class DodExplanationSerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()

    class Meta:
        model = MainPageDodExplanation
        fields = ['id', 'title', 'text', 'icon']

    def get_icon(self, obj):
        return obj.icon.url


class ThirdPartyMenuListSerializer(serializers.Serializer):
    faq = serializers.SerializerMethodField()
    notice = serializers.SerializerMethodField()
    suggestion = serializers.SerializerMethodField()
