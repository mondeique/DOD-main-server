from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, password, phone, **kwargs):
        if not phone:
            raise ValueError('핸드폰 번호를 입력해주세요')
        user = self.model(phone=phone, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone, password=None, **kwargs):
        kwargs.setdefault('is_staff', False)
        kwargs.setdefault('is_superuser', False)
        return self._create_user(password, phone, **kwargs)

    def create_superuser(self, password, phone, **kwargs):
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)

        if kwargs.get('is_staff') is not True:
            raise ValueError('superuser must have is_staff=True')
        if kwargs.get('is_superuser') is not True:
            raise ValueError('superuser must have is_superuser=True')
        return self._create_user(password, phone, **kwargs)


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=30, null=True, blank=True)
    uid = models.UUIDField(unique=True, null=True, blank=True, help_text="phone 대신 USERNAME_FIELD를 대체할 field입니다.")
    USERNAME_FIELD = 'uid'
    REQUIRED_FIELDS = ['phone']
    phone = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True, help_text="밴시 is_active = False")
    is_staff = models.BooleanField(default=False, help_text="super_user와의 권한 구분을 위해서 새로 만들었습니다. 일반적 운영진에게 부여됩니다.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    email = models.EmailField(max_length=100, unique=True, db_index=True, blank=True, null=True,
                              help_text="운영진 staff page에서 로그인 시 사용합니다.")
    objects = UserManager()

    def __str__(self):
        if self.is_anonymous:
            return 'anonymous'
        if self.is_staff:
            return '[staff] {}'.format(self.email)
        return self.phone


class PhoneConfirm(models.Model):
    """
    회원가입, 비밀번호 변경에만 사용하는 핸드폰 인증 모델입니다.
    설문자의 인증번호 모델은 따로 생성하여서 관리합니다.
    """
    SIGN_UP = 1
    RESET_PASSWORD = 2

    KINDS = (
        (SIGN_UP, '회원가입'),
        (RESET_PASSWORD, '비밀번호 변경'),
    )
    phone = models.CharField(max_length=20)
    confirm_key = models.CharField(max_length=4)
    kinds = models.IntegerField(choices=KINDS, default=1)
    is_confirmed = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
