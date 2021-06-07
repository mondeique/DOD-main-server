from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

# Create your models here.


class User(AbstractBaseUser):
    phone = models.CharField(max_length=20, blank=True, null=True, unique=True)
    is_active = models.BooleanField(default=True, help_text="탈퇴시 is_active = False")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PhoneConfirm(models.Model):
    SIGN_UP = 1
    RESET_PASSWORD = 2

    KINDS = (
        (SIGN_UP, '회원가입'),
        (RESET_PASSWORD, '비밀번호 변경'),
    )
    phone = models.CharField(max_length=20)
    certification_number = models.CharField(max_length=4)
    kinds = models.IntegerField(choices=KINDS, default=1)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
