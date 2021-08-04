from django.contrib import admin
from custom_manage.sites import staff_panel

# staff
from projects.models import Project, ProjectMonitoringLog


class ProjectStaffadmin(admin.ModelAdmin):
    list_display = ['id',
                    'name',
                    'owner',
                    'winner_count',
                    'project_hash_key',
                    'start_at',
                    'dead_at',
                    'status',
                    'is_active',
                    'draw_again',
                    'dead_line_notice']

    def draw_again(self, project):
        if not project.monitoring_logs.exists():
            return None
        return project.monitoring_logs.first().draw_again

    def dead_line_notice(self, project):
        if not project.monitoring_logs.exists():
            return None
        return project.monitoring_logs.first().dead_line_notice

    search_fields = ['project_hash_key', 'name', 'owner__phone']


class ProjectMonitoringStaffAdmin(admin.ModelAdmin):
    list_display = ['project', 'draw_again', 'dead_line_notice']


staff_panel.register(Project, ProjectStaffadmin)
staff_panel.register(ProjectMonitoringLog, ProjectMonitoringStaffAdmin)
