from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from notice.models import MainPageDodExplanation, FAQLink, NoticeLink, SuggestionLink, PrivacyPolicyLink, \
    TermsOfServiceLink, ContactLink
from notice.serializers import DodExplanationSerializer, ThirdPartyMenuListSerializer


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
            else FAQLink.objects.filter(is_active=True).last().link

        notice = None if not NoticeLink.objects.filter(is_active=True).exists()\
            else NoticeLink.objects.filter(is_active=True).last().link

        suggestion = None if not SuggestionLink.objects.filter(is_active=True).exists()\
            else SuggestionLink.objects.filter(is_active=True).last().link

        contact = None if not ContactLink.objects.filter(is_active=True).exists() \
            else ContactLink.objects.filter(is_active=True).last().link

        # privacy_policy = None if not PrivacyPolicyLink.objects.filter(is_active=True).exists() \
        #     else PrivacyPolicyLink.objects.filter(is_active=True).last().link
        #
        # terms_of_service = None if not TermsOfServiceLink.objects.filter(is_active=True).exists() \
        #     else TermsOfServiceLink.objects.filter(is_active=True).last().link

        return Response({'faq': faq,
                         'notice': notice,
                         'contact': contact,
                         'suggestion': suggestion}, status=status.HTTP_200_OK)
