from django.contrib import admin
from custom_manage.sites import staff_panel
from notice.models import LinkCopyNotice, FAQLink, ContactLink, MainPageDodExplanation


class LinkCopyNoticeStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title', 'is_active', 'created_at']


class FAQLinkStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'notion_link', 'is_active', 'created_at']


class ContactLinkStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'kakao_link', 'is_active', 'created_at']


class MainPageDodExplanationStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title', 'is_active', 'created_at']


staff_panel.register(LinkCopyNotice, LinkCopyNoticeStaffAdmin)
staff_panel.register(FAQLink, FAQLinkStaffAdmin)
staff_panel.register(ContactLink, ContactLinkStaffAdmin)
staff_panel.register(MainPageDodExplanation, MainPageDodExplanationStaffAdmin)
