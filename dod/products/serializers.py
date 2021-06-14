from rest_framework import serializers

from products.models import Product, Item


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


class ItemRetrieveSerializer(serializers.ModelSerializer):
    brand = serializers.SerializerMethodField()
    thumbnail_image = serializers.SerializerMethodField()
    discount_rate = serializers.SerializerMethodField()


    class Meta:
        model = Item
        fields = ['id', 'brand', 'name', 'thumbnail_image', 'price', 'origin_price', 'discount_rate']

    def get_brand(self, obj):
        if obj.brand:
            return obj.brand.name

    def get_thumbnail_image(self, obj):
        return obj.thumbnail.url

    def get_discount_rate(self, obj):
        discount_rate = round((obj.origin_price - obj.price) / obj.origin_price * 100)
        return discount_rate
