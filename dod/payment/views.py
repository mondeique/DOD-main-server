from django.shortcuts import render

# Create your views here.
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status

from core.slack import deposit_success_slack_message
from payment.models import DepositWithoutBankbookShortCutLink, DepositWithoutBankbookQRimage
from projects.models import Project


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


class DepositSuccessAPIView(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    permission_classes = [IsAuthenticated]
    queryset = Project.objects.filter(is_active=True)
    serializer_class = None

    def retrieve(self, request, *args, **kwargs):
        project = self.get_object()
        if project.owner != request.user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        message = "\n [입금확인요청] \n" \
                  "전화번호: {} \n" \
                  "프로젝트명: {} \n" \
                  "입금자명: {}\n" \
                  "결제금액: {}원\n" \
                  "--------------------".format(project.owner.phone,
                                     project.name,
                                     project.deposit_logs.first().depositor,
                                     project.deposit_logs.first().total_price)
        deposit_success_slack_message(message)
        return Response(status=status.HTTP_200_OK)

# TODO : BootPay
