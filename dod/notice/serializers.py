from rest_framework import serializers

from notice.models import LinkCopyNotice, MainPageDodExplanation, FAQLink, NoticeLink, SuggestionLink, \
    PrivacyPolicyLink, TermsOfServiceLink, ContactLink


class LinkNoticeSerializer(serializers.ModelSerializer):

    class Meta:
        model = LinkCopyNotice
        fields = ['id', 'title', 'content']


class DodExplanationSerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()

    class Meta:
        model = MainPageDodExplanation
        fields = ['id', 'title', 'text', 'icon', 'link_url']

    def get_icon(self, obj):
        return obj.icon.url


class MenuSerializer(serializers.ModelSerializer):
    icon_src = serializers.SerializerMethodField()

    class Meta:
        fields = ['id', 'icon_src', 'link']
        abstract = True

    def get_icon_src(self, obj):
        if obj.icon:
            return obj.icon.url
        return ''


class FAQMenuSerializer(MenuSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = FAQLink
        fields = MenuSerializer.Meta.fields + ['title']

    def get_title(self, obj):
        return '자주묻는질문'


class NoticeMenuSerializer(MenuSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = NoticeLink
        fields = MenuSerializer.Meta.fields + ['title']

    def get_title(self, obj):
        return '공지사항'


class SuggestionMenuSerializer(MenuSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = SuggestionLink
        fields = MenuSerializer.Meta.fields + ['title']

    def get_title(self, obj):
        return '건의하기'


class ContactMenuSerializer(MenuSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = ContactLink
        fields = MenuSerializer.Meta.fields + ['title']

    def get_title(self, obj):
        return '문의하기'


class ThirdPartyMenuListSerializer(serializers.Serializer):
    faq = serializers.SerializerMethodField()
    notice = serializers.SerializerMethodField()
    suggestion = serializers.SerializerMethodField()
    privacy_policy = serializers.SerializerMethodField()
    terms_of_service = serializers.SerializerMethodField()

    class Meta:
        fields = ['faq']

    def get_faq(self):
        if FAQLink.objects.filter(is_active=True).exists():
            return FAQLink.objects.filter(is_active=True).last().link
        else:
            return None

    def get_notice(self):
        if NoticeLink.objects.filter(is_active=True).exists():
            return NoticeLink.objects.filter(is_active=True).last().link
        else:
            return None

    def get_suggestion(self):
        if SuggestionLink.objects.filter(is_active=True).exists():
            return SuggestionLink.objects.filter(is_active=True).last().link
        else:
            return None

    def get_privacy_policy(self):
        if PrivacyPolicyLink.objects.filter(is_active=True).exists():
            return PrivacyPolicyLink.objects.filter(is_active=True).last().link
        else:
            return None

    def get_terms_of_service(self):
        if TermsOfServiceLink.objects.filter(is_active=True).exists():
            return TermsOfServiceLink.objects.filter(is_active=True).last().link
        else:
            return None
