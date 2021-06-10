from django.contrib.auth import (
    login as django_login,
    logout as django_logout,
    get_user_model)
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny

# Create your views here.
from accounts.models import User, PhoneConfirm
from accounts.serializers import LoginSerializer, SignupSerializer, \
    ResetPasswordSerializer, UserInfoSerializer


class AccountViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    permission_classes = [AllowAny, ]
    queryset = User.objects.filter(is_active=True)
    token_model = Token

    def get_serializer_class(self):
        if self.action == 'signup':
            serializer = SignupSerializer
        elif self.action == 'reset_pw':
            serializer = ResetPasswordSerializer
        elif self.action == 'login':
            serializer = LoginSerializer
        else:
            serializer = super(AccountViewSet, self).get_serializer_class()
        return serializer

    @transaction.atomic
    @action(methods=['post'], detail=False)
    def signup(self, request, *args, **kwargs):
        """
        회원가입시 사용하는 api 입니다.
        sms 인증이 완료될 때 return 된 phone, confirm_key에 + password 을 입력받습니다.
        confirm_key를 활용하여 외부 api로 signup을 방지하였습니다.
        api: POST accounts/v1/signup/
        :data:
        {'phone', 'confirm_key', 'password'}
        :return:
        400 : bad request
        400 : confirm_key가 유효하지 않을 때
        201 : created
        """

        # user 생성
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        serializer = UserInfoSerializer(user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _login(self):
        user = self.serializer.validated_data['user']
        setattr(user, 'backend', 'django.contrib.auth.backends.ModelBackend')
        django_login(self.request, user)
        # loginlog_on_login(request=self.request, user=user)

    @action(methods=['post'], detail=False)
    def login(self, request, *args, **kwargs):
        """
        api: POST accounts/v1/login/
        """
        try:
            self.serializer = self.get_serializer(data=request.data)
            self.serializer.is_valid(raise_exception=True)
            self._login()
            user = self.serializer.validated_data['user']
        except Exception as e:
            return Response({"non_field_errors": ['Failed to login.']},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = UserInfoSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False, url_name='logout')
    def logout(self, request):
        """
        api: POST accounts/v1/logout/
        header = {'Authorization' : token}
        data = {}
        :return: code, status
        """
        try:
            request.user.auth_token.delete()
        except (AttributeError, ObjectDoesNotExist):
            key = request.headers['Authorization']
            if key:
                token = Token.objects.get(key=key)
                token.delete()
        if getattr(settings, 'REST_SESSION_LOGIN', True):
            django_logout(request)

        return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def reset_pw(self, request, *args, **kwargs):
        """
        비밀번호 재설정에 사용하는 api 입니다.
        sms 인증이 완료될 때 return 된 phone, confirm_key에 + password 을 입력받습니다.
        api: POST accounts/v1/reset_pw/
        :return:
        400 : bad request
        400 : confirm_key가 유효하지 않을 때
        201 : created
        """
        data = request.data.copy()

        # check is confirmed (temp key로서 외부의 post 막음)
        # TODO : view를 serializer로 옮겨서 이쁘게 만들기
        confirm_key = data.get('confirm_key')
        if not confirm_key:
            return Response("No confirm key", status=status.HTTP_400_BAD_REQUEST)

        confirm_key = data.pop('confirm_key')
        phone_confirm = PhoneConfirm.objects.get(confirm_key=confirm_key)
        if not phone_confirm.is_confirmed:
            return Response("Unconfirmed phone number", status=status.HTTP_400_BAD_REQUEST)
        if phone_confirm.phone != data.get("phone"):
            return Response("Not match phone number & temp key", status=status.HTTP_400_BAD_REQUEST)

        phone = data.pop('phone')
        user = User.objects.filter(phone=phone, is_active=True)

        if user.count() == 0:
            return Response("User does not exist", status=status.HTTP_400_BAD_REQUEST)

        user = user.last()

        # password reset(update) 생성
        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        serializer = UserInfoSerializer(user)
        return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)

