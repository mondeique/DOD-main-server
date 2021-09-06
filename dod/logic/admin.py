from django.contrib import admin
from custom_manage.sites import staff_panel
from logic.models import DateTimeLotteryResult, PercentageResult, DODAveragePercentage, DODExtraAveragePercentage


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


class PercentageResultStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'project_name', 'project_key', 'percentage', 'is_used', 'created_at']

    def project_name(self, obj):
        if hasattr(obj.logic, 'project'):
            return obj.logic.project.name
        return None

    def project_key(self, obJ):
        if hasattr(obJ.logic, 'project'):
            return obJ.logic.project.project_hash_key
        return None


class DODAveragePercentageStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'average', 'created_at', 'updated_at']

    def average(self, obj):
        return str(obj.average_percentage) + '%'


class DODExtraAveragePercentageStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'average', 'created_at', 'updated_at']

    def average(self, obj):
        return str(obj.extra_average_percentage) + '%'


staff_panel.register(DateTimeLotteryResult, DateTimeLotteryResultStaffAdmin)
staff_panel.register(PercentageResult, PercentageResultStaffAdmin)
staff_panel.register(DODAveragePercentage, DODAveragePercentageStaffAdmin)
staff_panel.register(DODExtraAveragePercentage, DODExtraAveragePercentageStaffAdmin)
