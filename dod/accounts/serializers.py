import random
import string
import uuid

from django.db.models import Avg
from rest_framework import serializers, exceptions
from accounts.models import User
from rest_framework.authtoken.models import Token
from django.utils.translation import ugettext_lazy as _


def generate_random_key(length=10):
    return ''.join(random.choices(string.digits+string.ascii_letters, k=length))


def create_token(token_model, user):
    token, _ = token_model.objects.get_or_create(user=user)
    return token


class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("phone", "password")

    def validate(self, attrs):
        phone = attrs.get('phone')
        # Did we get back an active user?
        if User.objects.filter(phone=phone, is_active=True):
            msg = _('User is already exists.')
            raise exceptions.ValidationError(msg) # already exists
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            phone=validated_data['phone'],
        )
        user.set_password(validated_data['password'])
        user.uid = uuid.uuid4()
        user.save()
        return user

    def update(self, instance, validated_data):
        if validated_data.get('phone'):
            instance.phone = validated_data['phone']
        if validated_data.get('password'):
            instance.set_password(validated_data['password'])
        instance.save()
        return instance


class ResetPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("phone", "password")

    def update(self, instance, validated_data):
        if validated_data.get('password'):
            instance.set_password(validated_data['password'])
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        from django.contrib.auth.hashers import check_password
        super(LoginSerializer, self).validate(attrs)
        phone = attrs.get('phone')
        password = attrs.get('password')

        if phone is None:
            return

        user = User.objects.filter(phone=phone, is_active=True).last()
        attrs['user'] = user

        if user:
            valid_password = check_password(password, user.password)
            if valid_password:
                token, _ = Token.objects.get_or_create(user=user)
                attrs['token'] = token.key
                return attrs
            raise exceptions.ValidationError("invalid Password")
        raise exceptions.ValidationError("invalid Email (No User)")


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ('key',)


class UserInfoSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'token', 'name']

    def get_token(self, user):
        token = create_token(Token, user)
        return token.key
