from django.contrib import admin
from custom_manage.sites import staff_panel
from payment.models import UserDepositLog, DepositWithoutBankbookShortCutLink, DepositWithoutBankbookQRimage, \
    DepositWithoutBankbookNotice


class UserDepositLogStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'project', 'total_price', 'depositor', 'confirm']
    list_editable = ['confirm']


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
