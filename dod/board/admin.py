from django.contrib import admin

from board.models import Board
from custom_manage.sites import staff_panel


class BoardStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title', 'reward_text', 'is_dod', 'owner', 'is_active']


staff_panel.register(Board, BoardStaffAdmin)
