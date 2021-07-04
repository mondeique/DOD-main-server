from rest_framework import serializers


class PaymentSerializer(serializers.Serializer):
    project = serializers.IntegerField()
    price = serializers.IntegerField()
    application_id = serializers.IntegerField()  # 1: web, 2:android, 3:ios
