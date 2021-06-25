from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from notice.models import MainPageDodExplanation, FAQLink, NoticeLink, SuggestionLink, PrivacyPolicyLink, \
    TermsOfServiceLink, ContactLink
from notice.serializers import DodExplanationSerializer, ThirdPartyMenuListSerializer, FAQMenuSerializer, \
    NoticeMenuSerializer, SuggestionMenuSerializer, ContactMenuSerializer


class DodExplanationAPIView(viewsets.GenericViewSet,
                            mixins.ListModelMixin,):
    permission_classes = [AllowAny]
    queryset = MainPageDodExplanation.objects.filter(is_active=True).order_by('id')
    serializer_class = DodExplanationSerializer
    pagination_class = None
    """
    대시보드 없는 메인페이지의 dod 설명 api 입니다.
    """
    def list(self, request, *args, **kwargs):
        """
        api : api/v1/dod-explanation/
        """

        return super(DodExplanationAPIView, self).list(request, args, kwargs)


class ThirdPartyMenuListAPIView(viewsets.GenericViewSet,
                                mixins.ListModelMixin):
    queryset = None
    serializer_class = None
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        faq = None if not FAQLink.objects.filter(is_active=True).exists()\
            else FAQLink.objects.filter(is_active=True).last()

        notice = None if not NoticeLink.objects.filter(is_active=True).exists()\
            else NoticeLink.objects.filter(is_active=True).last()

        suggestion = None if not SuggestionLink.objects.filter(is_active=True).exists()\
            else SuggestionLink.objects.filter(is_active=True).last()

        contact = None if not ContactLink.objects.filter(is_active=True).exists() \
            else ContactLink.objects.filter(is_active=True).last()

        menu_list = [faq, contact, suggestion, notice]
        menu_data = []
        for menu in menu_list:
            if menu:
                menu_data.append(self._meta_serializer(menu))

        return Response(menu_data, status=status.HTTP_200_OK)

    def _meta_serializer(self, obj):
        val = {'icon_src': obj.icon.url,
               'link': obj.link}
        obj_name = obj._meta.model_name
        if obj_name == 'faqlink':
            title = '자주 묻는 질문'
        elif obj_name == 'contactlink':
            title = '문의·상담하기'
        elif obj_name == 'suggestionlink':
            title = '건의하기'
        elif obj_name == 'noticelink':
            title = '공지사항'
        else:
            title = None
        val['title'] = title
        return val


