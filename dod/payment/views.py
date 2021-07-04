from django.shortcuts import render, get_object_or_404

# Create your views here.
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from rest_framework import exceptions

from core.slack import deposit_success_slack_message, bootpay_feedback_slack_message
from payment.Bootpay import BootpayApi
from payment.loader import load_credential
from payment.models import DepositWithoutBankbookShortCutLink, DepositWithoutBankbookQRimage
from payment.serializers import PaymentSerializer
from products.models import Product
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
    permission_classes = [AllowAny]
    queryset = Project.objects.filter(is_active=True)
    serializer_class = None

    def retrieve(self, request, *args, **kwargs):
        project = self.get_object()

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


class BootpayFeedbackAPIView(APIView):

    def post(self, request, *args, **kwargs):
        data = request.data
        name = data.get('name', '')
        price = data.get('price', '')
        method_name = data.get('method_name', '')
        msg = data
        bootpay_feedback_slack_message(msg)
        return Response(status=status.HTTP_200_OK)

# TODO : BootPay


class PaymentViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    queryset = Product.objects.all().select_related('project')
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(PaymentViewSet, self).__init__(*args, **kwargs)
        self.data = None
        self.serializer = None
        self.products = None
        self.user = None
        self.project = None

    @staticmethod
    def get_access_token():
        bootpay = BootpayApi(application_id=load_credential("rest_application_id"),
                             private_key=load_credential("private_key"))
        result = bootpay.get_access_token()
        if result['status'] is 200:
            return bootpay
        else:
            raise exceptions.APIException(detail='bootpay access token 확인바람')

    def create(self, request, *args, **kwargs):
        """
        boot pay 결제 시작
        api: POST api/v1/payment/

        :param request: project_id, price(total), application_id(?) 무조건 웹이지만?

        :return: result {payform}
        """
        self.data = request.data.copy()
        self.user = request.user
        self.serializer = self.get_serializer(data=self.data)
        self.serializer.is_valid(raise_exception=True)

        self.project = get_object_or_404(Project, pk=self.serializer.validated_data['project'])
        self.products = self.get_queryset().filter(project=self.project)

        self.check_owner()


    def check_owner(self):
        if self.project.owner != self.user:
            raise exceptions.NotAcceptable(detail='결제자 정보가 다릅니다.')

    def check_price(self):
        pass


    def check_product_filled(self):
        # 추후 기프티콘을 채운다면 사용할 예정
        # 만약 자동발송이라면 사용 안함
        pass



