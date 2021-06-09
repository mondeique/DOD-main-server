from rest_framework import serializers

from products.models import Product


class ProductCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ['project', 'item', 'count']


class ProductSimpleDashboardSerializer(serializers.ModelSerializer):
    item_thumbnail = serializers.SerializerMethodField()
    present_winner_count = serializers.SerializerMethodField()
    winner_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'item_thumbnail', 'present_winner_count', 'winner_count']

    def get_item_thumbnail(self, obj):
        item = obj.item
        return item.thumbnail.url

    def get_present_winner_count(self, obj):
        rewards = obj.rewards.filter(winner_id__isnull=False).count()
        return rewards

    def get_winner_count(self, obj):
        return obj.count

