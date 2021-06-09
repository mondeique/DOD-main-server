from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from notice.models import MainPageDodExplanation
from notice.serializers import DodExplanationSerializer


class DodExplanationAPIView(viewsets.GenericViewSet,
                            mixins.ListModelMixin,):
    permission_classes = [AllowAny]
    queryset = MainPageDodExplanation.objects.filter(is_active=True).order_by('id')
    serializer_class = DodExplanationSerializer
    """
    대시보드 없는 메인페이지의 dod 설명 api 입니다.
    """
    def list(self, request, *args, **kwargs):
        """
        api : api/v1/dod-explanation/
        """

        return super(DodExplanationAPIView, self).list(request, args, kwargs)
