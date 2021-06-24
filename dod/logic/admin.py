from django.contrib import admin
from custom_manage.sites import staff_panel
from logic.models import DateTimeLotteryResult


class DateTimeLotteryResultStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'project_name', 'project_key', 'lucky_time', 'is_used', 'created_at']

    def project_name(self, obj):
        if hasattr(obj.logic, 'project'):
            return obj.logic.project.name
        return None

    def project_key(self, obJ):
        if hasattr(obJ.logic, 'project'):
            return obJ.logic.project.project_hash_key
        return None


staff_panel.register(DateTimeLotteryResult, DateTimeLotteryResultStaffAdmin)
