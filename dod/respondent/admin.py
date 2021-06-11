from django.contrib import admin
from custom_manage.sites import staff_panel

# staff
from projects.models import Project
from respondent.models import RespondentPhoneConfirm, Respondent


class RespondentPhoneConfirmStaffadmin(admin.ModelAdmin):
    list_display = ['id',
                    'phone',
                    'confirm_key',
                    'is_confirmed',
                    'created_at',
                    ]



class RespondentStaffadmin(admin.ModelAdmin):
    list_display = ['id',
                    'project',
                    'phone_confirm',
                    'is_win',
                    ]


staff_panel.register(RespondentPhoneConfirm, RespondentPhoneConfirmStaffadmin)
staff_panel.register(Respondent, RespondentStaffadmin)
