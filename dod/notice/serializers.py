from rest_framework import serializers

from notice.models import LinkCopyNotice


class LinkNoticeSerializer(serializers.ModelSerializer):

    class Meta:
        model = LinkCopyNotice
        fields = ['id', 'title', 'content']
