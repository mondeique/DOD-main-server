from django.contrib import admin
from django.contrib.auth.models import Permission
from django import forms
from rest_framework.authtoken.models import Token
from custom_manage.sites import superadmin_panel, staff_panel
from custom_manage.tools import superadmin_register

from accounts.models import User, PhoneConfirm


class UserSuperadminForm(forms.ModelForm):
    user_permissions = forms.ModelMultipleChoiceField(
        Permission.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple('user_permissions', False),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(UserSuperadminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['user_permissions'] = self.instance.user_permissions.values_list('pk', flat=True)


class UserSuperadmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'is_active']
    search_fields = ['email', 'phone']
    form = UserSuperadminForm
    actions = ['apply_staff_permission']

    def apply_staff_permission(self, request, queryset):
        park = User.objects.get(pk=2)
        permission_object_ids = park.user_permissions.all().values_list('id', flat=True)
        rows_updated = 0
        for user in queryset.exclude(id=park.id):
            user.user_permissions.clear()
            user.user_permissions.add(*permission_object_ids)
            rows_updated += 1
        self.message_user(request, '%d개의 아이디에 staff 권한을 적용했습니다.' % rows_updated)


class TokenStaffAdmin(admin.ModelAdmin):
    list_display = ['key', 'user', 'created']


superadmin_panel.register(User, UserSuperadmin)
superadmin_panel.register(Token, TokenStaffAdmin)
superadmin_register(PhoneConfirm, list_display=['phone', 'confirm_key', 'is_confirmed', 'created_at'])


# staff

class UserStaffadmin(admin.ModelAdmin):
    list_display = ['id', 'phone', 'email', 'is_active', 'created_at']
    search_fields = ['email', 'phone']


class PhoneConfirmAdmin(admin.ModelAdmin):
    list_display = ['phone', 'confirm_key', 'is_confirmed', 'is_used', 'created_at']


staff_panel.register(User, UserStaffadmin)
staff_panel.register(PhoneConfirm, PhoneConfirmAdmin)
staff_panel.register(Token, TokenStaffAdmin)
