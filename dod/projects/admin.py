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
                    'is_active']

    search_fields = ['project_hash_key', 'name', 'owner__phone']


staff_panel.register(Project, ProjectStaffadmin)
