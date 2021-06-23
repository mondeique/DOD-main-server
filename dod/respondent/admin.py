from django.contrib import admin
from custom_manage.sites import staff_panel

# staff
from respondent.models import RespondentPhoneConfirm, Respondent, DeviceMetaInfo


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


class DeviceMetaInfoStaffAdmin(admin.ModelAdmin):
    list_display = ['ip', 'user_agent', 'validator', 'is_confirmed', 'created_at']


staff_panel.register(RespondentPhoneConfirm, RespondentPhoneConfirmStaffadmin)
staff_panel.register(Respondent, RespondentStaffadmin)
staff_panel.register(DeviceMetaInfo, DeviceMetaInfoStaffAdmin)
