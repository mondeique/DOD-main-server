from django.contrib import admin

from custom_manage.sites import staff_panel
from payment.models import UserDepositLog, DepositWithoutBankbookShortCutLink, DepositWithoutBankbookQRimage, \
    DepositWithoutBankbookNotice


class UserDepositNameListFilter(admin.SimpleListFilter):

    title = 'Has depositor'

    parameter_name = 'has_depositor'

    def lookups(self, request, model_admin):

        return (
            ('yes', 'Yes'),
            ('no',  'No'),
        )

    def queryset(self, request, queryset):

        if self.value() == 'yes':
            return queryset.filter(depositor__isnull=False).exclude(depositor='')

        if self.value() == 'no':
            return queryset.filter(depositor__isnull=True)


class UserDepositLogStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'project', 'project_key', 'total_price', 'depositor', 'confirm', 'created_at']
    list_editable = ['confirm']
    search_fields = ['project__project_hash_key']
    list_filter = [UserDepositNameListFilter]

    def project_key(self, obj):
        if obj.project:
            return obj.project.project_hash_key
        return ''


class DepositWithoutBankbookShortCutLinkStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'company_name', 'link', 'is_active', 'created_at']
    list_editable = ['is_active']


class DepositWithoutBankbookQRimageStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'company_name', 'qr_img', 'is_active', 'created_at']
    list_editable = ['is_active']


class DepositWithoutBankbookNoticeStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title', 'is_active', 'created_at']
    list_editable = ['is_active']


staff_panel.register(UserDepositLog, UserDepositLogStaffAdmin)
staff_panel.register(DepositWithoutBankbookShortCutLink, DepositWithoutBankbookShortCutLinkStaffAdmin)
staff_panel.register(DepositWithoutBankbookQRimage, DepositWithoutBankbookQRimageStaffAdmin)
staff_panel.register(DepositWithoutBankbookNotice, DepositWithoutBankbookNoticeStaffAdmin)
