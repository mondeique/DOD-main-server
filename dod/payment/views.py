from django.shortcuts import render

# Create your views here.
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status

from payment.models import DepositWithoutBankbookShortCutLink, DepositWithoutBankbookQRimage


class DepositInfoAPIView(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        """
        api : api/v1/deposit-info/
        return : {'qr_code', 'url'}
        """
        url = DepositWithoutBankbookShortCutLink.objects.filter(is_active=True).last().link
        qr_code = DepositWithoutBankbookQRimage.objects.filter(is_active=True).last().qr_img.url
        return Response({'qr_code': qr_code,
                         'url': url}, status=status.HTTP_200_OK)


# TODO : BootPay
