import random
import string
import uuid

from django.db.models import Avg
from rest_framework import serializers, exceptions
from accounts.models import User, PhoneConfirm
from rest_framework.authtoken.models import Token
from django.utils.translation import ugettext_lazy as _


def generate_random_key(length=10):
    return ''.join(random.choices(string.digits+string.ascii_letters, k=length))


def create_token(token_model, user):
    token, _ = token_model.objects.get_or_create(user=user)
    return token


class SignupSerializer(serializers.ModelSerializer):
    confirm_key = serializers.CharField()

    class Meta:
        model = User
        fields = ("phone", "password", "confirm_key")

    def validate(self, attrs):
        phone = attrs.get('phone')
        confirm_key = attrs.get('confirm_key')
        phone_confirm_qs = PhoneConfirm.objects.filter(confirm_key=confirm_key)

        if User.objects.filter(phone=phone, is_active=True):
            msg = _('이미 가입된 계정이 있습니다.')
            raise exceptions.ValidationError(msg)
        if not phone_confirm_qs.exists():
            msg = _('잘못된 인증번호입니다.')
            raise exceptions.ValidationError(msg)

        phone_confirm = phone_confirm_qs.last()
        if not phone_confirm.is_confirmed:
            msg = _('인증되지 않은 핸드폰번호 입니다.')
            raise exceptions.ValidationError(msg)
        if phone_confirm.phone != phone:
            msg = _('잘못된 인증번호로 요청하였습니다.')
            raise exceptions.ValidationError(msg)
        if phone_confirm.is_used:
            msg = _('이미 사용된 인증번호 입니다.')
            raise exceptions.ValidationError(msg)
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            phone=validated_data['phone'],
        )
        user.set_password(validated_data['password'])
        user.uid = uuid.uuid4()
        user.save()

        self.confirm_key = validated_data['confirm_key']
        self._phone_confirm_is_used()

        return user

    def update(self, instance, validated_data):
        if validated_data.get('phone'):
            instance.phone = validated_data['phone']
        if validated_data.get('password'):
            instance.set_password(validated_data['password'])
        instance.save()

        self.confirm_key = validated_data['confirm_key']
        self._phone_confirm_is_used()

        return instance

    def _phone_confirm_is_used(self):
        confirm_key = self.confirm_key
        phone_confirm = PhoneConfirm.objects.get(confirm_key=confirm_key)
        phone_confirm.is_used = True
        phone_confirm.save()


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
            raise exceptions.ValidationError("잘못된 비밀번호입니다.")
        raise exceptions.ValidationError("계정이 존재하지 않습니다.")


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


class SMSSignupPhoneCheckSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate(self, attrs):
        super(SMSSignupPhoneCheckSerializer, self).validate(attrs)
        phone = attrs.get('phone')
        if User.objects.filter(phone=phone, is_active=False).exists():
            msg = _('활성화 되지않은 유저입니다.')
            raise exceptions.ValidationError(msg)
        elif User.objects.filter(phone=phone, is_active=True).exists():
            msg = _('이미 가입된 정보가 있습니다.')
            raise exceptions.ValidationError(msg)
        return attrs


class SMSSignupPhoneConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField()
    confirm_key = serializers.CharField()

    def validate(self, attrs):
        super(SMSSignupPhoneConfirmSerializer, self).validate(attrs)
        phone = attrs.get('phone')
        confirm_key = attrs.get('confirm_key')
        phone_confirm = PhoneConfirm.objects.filter(phone=phone, is_confirmed=False)
        if not phone_confirm.exists():
            msg = _('다시한번 인증번호를 요청해 주세요')
            raise exceptions.ValidationError(msg)
        if PhoneConfirm.objects.filter(phone=phone, is_confirmed=True, confirm_key=confirm_key).exists():
            msg = _('이미 인증되었습니다.')
            raise exceptions.ValidationError(msg)
        elif not phone_confirm.filter(confirm_key=confirm_key).exists():
            msg = _('잘못된 인증번호 입니다.')
            raise exceptions.ValidationError(msg)

        phone_confirm = phone_confirm.get(confirm_key=confirm_key)
        phone_confirm.is_confirmed = True
        phone_confirm.save()
        return attrs


