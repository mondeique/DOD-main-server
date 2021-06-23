from django.contrib import admin
from custom_manage.sites import staff_panel
from logs.models import MMSSendLog


class MMSSendLogsStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'code', 'phone', 'item_name', 'created_at', 'resend']


staff_panel.register(MMSSendLog, MMSSendLogsStaffAdmin)
