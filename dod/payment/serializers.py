from rest_framework import serializers

from payment.loader import load_credential
from payment.models import Payment
from products.models import Item, Product


class PaymentSerializer(serializers.Serializer):
    project = serializers.IntegerField()
    price = serializers.IntegerField()


# payment 에 사용되는 serializer
class ProductSerializer(serializers.ModelSerializer):
    item_name = serializers.SerializerMethodField()
    unique = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    qty = serializers.IntegerField(default=1)

    class Meta:
        model = Product
        fields = ('item_name', 'unique', 'price', 'qty')

    def get_item_name(self, obj):
        return obj.item.name

    def get_unique(self, obj):
        return str(obj.item.pk)

    def get_price(self, obj):
        return obj.price


class PayformSerializer(serializers.ModelSerializer):
    application_id = serializers.SerializerMethodField()
    order_id = serializers.IntegerField(source='id')
    items = serializers.SerializerMethodField()
    user_info = serializers.SerializerMethodField()
    pg = serializers.CharField(default='welcome')
    method = serializers.CharField(default='digital_card')

    class Meta:
        model = Payment
        fields = ['price', 'application_id', 'name', 'pg', 'method', 'items', 'user_info', 'order_id']

    def get_items(self, obj):
        products = self.context['products']
        return ProductSerializer(products, many=True).data

    def get_user_info(self, obj):
        return {
            'phone': obj.user.phone
        }

    def get_application_id(self, obj):
        return load_credential("bootpay", "")['application_id']


class PaymentConfirmSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    receipt_id = serializers.CharField()


class PaymentDoneSerialzier(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'remain_price', 'tax_free', 'remain_tax_free',
            'cancelled_price', 'cancelled_tax_free',
            'requested_at', 'purchased_at', 'status'
        ]

class PaymentCancelSerialzier(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'remain_price', 'remain_tax_free',
            'cancelled_price', 'cancelled_tax_free',
            'revoked_at', 'status'
        ]
