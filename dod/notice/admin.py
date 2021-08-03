from django.contrib import admin
from custom_manage.sites import staff_panel
from notice.models import LinkCopyNotice, FAQLink, ContactLink, MainPageDodExplanation, SuggestionLink, \
    PrivacyPolicyLink, TermsOfServiceLink, NoticeLink, TestGoogleFormsUrl


class LinkCopyNoticeStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'kinds', 'title', 'is_active', 'created_at']


class NoticeLinkStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'icon', 'link', 'is_active', 'created_at']


class FAQLinkStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'icon', 'link', 'is_active', 'created_at']


class ContactLinkStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'icon', 'link', 'is_active', 'created_at']


class SuggestionLinkStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'icon', 'link', 'is_active', 'created_at']


class PrivacyPolicyLinkStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'link', 'is_active', 'created_at']


class TermsOfServiceLinkStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'link', 'is_active', 'created_at']


class MainPageDodExplanationStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'order', 'title', 'is_active', 'created_at']


class TestGoogleFormsUrlStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'forms_url', 'is_active', 'created_at']


staff_panel.register(LinkCopyNotice, LinkCopyNoticeStaffAdmin)
staff_panel.register(FAQLink, FAQLinkStaffAdmin)
staff_panel.register(NoticeLink, NoticeLinkStaffAdmin)
staff_panel.register(ContactLink, ContactLinkStaffAdmin)
staff_panel.register(SuggestionLink, SuggestionLinkStaffAdmin)
staff_panel.register(PrivacyPolicyLink, PrivacyPolicyLinkStaffAdmin)
staff_panel.register(TermsOfServiceLink, TermsOfServiceLinkStaffAdmin)
staff_panel.register(MainPageDodExplanation, MainPageDodExplanationStaffAdmin)
staff_panel.register(TestGoogleFormsUrl, TestGoogleFormsUrlStaffAdmin)
