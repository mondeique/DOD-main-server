from django.contrib import admin
from custom_manage.sites import staff_panel

# staff
from projects.models import Project


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
        return project.monitoring_logs.first().draw_again

    def dead_line_notice(self, project):
        return project.monitoring_logs.first().dead_line_notice

    search_fields = ['project_hash_key', 'name', 'owner__phone']


staff_panel.register(Project, ProjectStaffadmin)
