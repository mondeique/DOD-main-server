from django.contrib import admin
from custom_manage.sites import staff_panel
from logic.models import DateTimeLotteryResult


class DateTimeLotteryResultStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'project_name', 'lucky_time', 'is_used', 'created_at']

    def project_name(self, obj):
        if hasattr(obj.logic, 'project'):
            return obj.logic.project.name
        return None


staff_panel.register(DateTimeLotteryResult, DateTimeLotteryResultStaffAdmin)
