from django.contrib import admin
from custom_manage.sites import staff_panel
from logic.models import DateTimeLotteryResult
from notice.models import LinkCopyNotice, FAQLink, ContactLink, MainPageDodExplanation


class DateTimeLotteryResultStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'lucky_time', 'is_used', 'created_at']


staff_panel.register(DateTimeLotteryResult, DateTimeLotteryResultStaffAdmin)

