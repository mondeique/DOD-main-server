from django.contrib import admin
from custom_manage.sites import staff_panel

# staff
from respondent.models import RespondentPhoneConfirm, Respondent, DeviceMetaInfo, TestRespondentPhoneConfirm, \
    TestRespondent


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
                    'project_key',
                    'phone_confirm',
                    'is_win',
                    ]

    def project_key(self, obj):
        if obj.project:
            return obj.project.project_hash_key
        return ''


class DeviceMetaInfoStaffAdmin(admin.ModelAdmin):
    list_display = ['ip', 'user_agent', 'validator', 'is_confirmed', 'created_at']


staff_panel.register(RespondentPhoneConfirm, RespondentPhoneConfirmStaffadmin)
staff_panel.register(TestRespondentPhoneConfirm, RespondentPhoneConfirmStaffadmin)
staff_panel.register(Respondent, RespondentStaffadmin)
staff_panel.register(TestRespondent, RespondentStaffadmin)
staff_panel.register(DeviceMetaInfo, DeviceMetaInfoStaffAdmin)
