from django.db import transaction
from django.shortcuts import render, get_object_or_404

# Create your views here.
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from rest_framework import exceptions
from rest_framework.decorators import authentication_classes, action

from core.slack import deposit_success_slack_message, bootpay_feedback_slack_message
from payment.Bootpay import BootpayApi
from payment.loader import load_credential
from payment.models import DepositWithoutBankbookShortCutLink, DepositWithoutBankbookQRimage, Payment, PaymentErrorLog
from payment.serializers import PaymentSerializer, PayformSerializer, PaymentConfirmSerializer, PaymentDoneSerialzier, \
    PaymentCancelSerialzier
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

def pay_test(request):
    return render(request, 'pay_test.html')


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
        self.payment = None

    @staticmethod
    def get_access_token():
        secrets = load_credential("bootpay", "")
        bootpay = BootpayApi(application_id=secrets["rest_application_id"],
                             private_key=secrets["private_key"])
        result = bootpay.get_access_token()
        if result['status'] is 200:
            return bootpay
        else:
            raise exceptions.APIException(detail='bootpay access token 확인바람')

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        boot pay 결제 시작
        api: POST api/v1/payment/

        :param request: project, price(total)

        :return: result {payform}
        """
        self.data = request.data.copy()
        self.user = request.user
        self.serializer = self.get_serializer(data=self.data)
        self.serializer.is_valid(raise_exception=True)

        self.project = get_object_or_404(Project, pk=self.serializer.validated_data['project'])
        self.products = self.get_queryset().filter(project=self.project)

        self.check_owner()
        self.check_price()

        with transaction.atomic():
            self.create_payment()

        serializer = PayformSerializer(self.payment, context={
            'products': self.products
        })
        return Response({'results': serializer.data}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def confirm(self, request):
        """
        bootpay 결제 확인 : 재고 등
        api: POST api/v1/payment/confirm/
        :param request: order_id(payment id와 동일), receipt_id(결제 영수증과 같은 개념:pg 사 발행)
        :return: code and status
        """
        serializer = PaymentConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = Payment.objects.get(pk=serializer.validated_data['order_id'])

        # payment : 결제 승인 전
        payment.receipt_id = serializer.validated_data['receipt_id']
        payment.status = 2
        payment.save()

        return Response(status=status.HTTP_200_OK)

    @transaction.atomic
    @action(methods=['post'], detail=False)
    def done(self, request):
        """
        bootpay 결제 완료시 호출되는 api 입니다.
        api: POST api/v1/payment/done/
        :param request: order_id(payment id와 동일), receipt_id(결제 영수증과 같은 개념:pg 사 발행)
        :return: status, code
        * receipt_id와 order_id로 payment를 못 찾을 시 payment와 trades의 status를 조정할 알고리즘 필요
        * front에서 제대로 값만 잘주면 문제될 것은 없지만,
        * https://docs.bootpay.co.kr/deep/submit 해당 링크를 보고 서버사이드 결제승인으로 바꿀 필요성 있음
        * https://github.com/bootpay/server_python/blob/master/lib/BootpayApi.py 맨 밑줄
        """
        receipt_id = request.data.get('receipt_id', None)
        order_id = request.data.get('order_id', None)
        if not (receipt_id or order_id):
            PaymentErrorLog.objects.create(user=request.user, temp_payment=request.user.payment_set.last(),
                                           description='(환불안됨)[결제 완료 중 에러] 잘못된 정보. 결제는 되었으니 부트페이 확인 필요',
                                           bootpay_receipt_id=request.user.payment_set.last().receipt_id)
            raise exceptions.NotAcceptable(detail='request body is not validated')

        try:
            payment = Payment.objects.get(id=order_id)
        except Payment.DoesNotExist:
            # 이런 경우는 없겠지만, payment 를 찾지 못한다면, User의 마지막 생성된 payment로 생각하고 에러 로그 생성
            PaymentErrorLog.objects.create(user=request.user, temp_payment=request.user.payment_set.last(),
                                           description='(환불안됨)[결제 완료 중 에러] 해당 payment 없음. 결제는 되었으니 부트페이 확인 필요',
                                           bootpay_receipt_id=receipt_id)
            raise exceptions.NotFound(detail='해당 order_id의 payment가 존재하지 않습니다.')

            # 결제 승인 중 (부트페이에선 결제 되었지만, done api 에서 처리 전)
        payment.status = 3
        payment.save()

        bootpay = self.get_access_token()
        result = bootpay.verify(receipt_id)
        if result['status'] == 200:
            # 성공!
            if int(result['data']['status']) == 1 and int(payment.price) == int(result['data']['price']):
                serializer = PaymentDoneSerialzier(payment, data=result['data'])
                if serializer.is_valid():
                    serializer.save()

                    # product status 2번처리 : 결제완료
                    products = Product.objects.filter(project__payment=payment)
                    products.update(status=1)

                    # payment : 결제 완료
                    payment.status = 1
                    payment.save()

                    # Project 활성화
                    project = payment.project
                    project.status = True
                    project.is_active = True
                    project.save()

                    return Response(status.HTTP_200_OK)
            else:
                # payment : 결제 승인 실패
                payment.status = -2
                payment.save()

                # bootpay 취소 요청
                result = bootpay.cancel(receipt_id, '{}'.format(payment.price), '디오디', '디오디 서버 결제승인 실패로 인한 결제취소')
                serializer = PaymentCancelSerialzier(payment, data=result['data'])

                if serializer.is_valid():
                    serializer.save()
                    PaymentErrorLog.objects.create(user=request.user, temp_payment=payment,
                                                   description='(환불완료)[결제 완료 중 에러] bootpay 결제 실패, *취소 완료',
                                                   is_refunded=True)

                    # trade : bootpay 환불 완료
                    Product.objects.filter(project__payment=payment).update(status=2)  # 결제되었다가 취소이므로 환불.

                    # payment : 결제 취소 완료
                    payment.status = 20
                    payment.save()

                    return Response({'detail': 'canceled'}, status=status.HTTP_200_OK)
                else:
                    PaymentErrorLog.objects.create(user=request.user, temp_payment=payment,
                                                   description='(환불안됨)[결제 완료 중 에러] bootpay 결제 되었지만 서버에러로 취소 요청 중 실패.'
                                                               ' 부트페이 확인 후 처리 필요.',
                                                   bootpay_receipt_id=receipt_id)

                    # 결제취소실패
                    payment.status = -20
                    payment.save()

        else:
            # payment : 결제 승인 실패
            payment.status = -2
            payment.save()

            # bootpay 취소 요청
            result = bootpay.cancel(receipt_id, '{}'.format(payment.price), '디오디', '디오디 서버 결제승인 실패로 인한 결제취소')
            serializer = PaymentCancelSerialzier(payment, data=result['data'])

            if serializer.is_valid():
                serializer.save()
                PaymentErrorLog.objects.create(user=request.user, temp_payment=payment,
                                               description='(환불완료)[결제 완료 중 에러] bootpay 결제 실패, *취소 완료', is_refunded=True)

                # trade : bootpay 환불 완료
                Product.objects.filter(project__payment=payment).update(status=2)  # 결제되었다가 취소이므로 환불.

                # payment : 결제 취소 완료
                payment.status = 20
                payment.save()

                return Response({'detail': 'canceled'}, status=status.HTTP_200_OK)
            else:
                PaymentErrorLog.objects.create(user=request.user, temp_payment=payment,
                                               description='(환불안됨)[결제 완료 중 에러] bootpay 결제 되었지만 서버에러로 취소 요청 중 실패.'
                                                           ' 부트페이 확인 후 처리 필요.',
                                               bootpay_receipt_id=receipt_id)

                # 결제취소실패
                payment.status = -20
                payment.save()

        return Response({'detail': ''}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def cancel(self, request):
        """
        결제 진행 취소 시 client 에서 호출하는 api 입니다.
        상품 상태를 초기화 합니다.
        api: POST api/v1/payment/cancel/
        :param request: order_id(payment id와 동일)
        """
        payment = Payment.objects.get(pk=request.data.get('order_id'))
        bootpay = self.get_access_token()
        result = bootpay.cancel(payment.receipt_id, '{}'.format(payment.price), '디오디', '결제취소')
        serializer = PaymentCancelSerialzier(payment, data=result['data'])

        # 결제취소진행중
        payment.status = -30
        payment.save()

        if serializer.is_valid():
            serializer.save()

            # trade : bootpay 환불 완료
            Product.objects.filter(project__payment=payment).update(status=2)  # 결제되었다가 취소이므로 환불.

            # payment : 결제 취소 완료
            payment.status = 20
            payment.save()

            return Response({'detail': 'canceled'}, status=status.HTTP_200_OK)
        else:
            PaymentErrorLog.objects.create(user=request.user, temp_payment=payment,
                                           description='(환불안됨)[결제 취소 중 에러] 결제취소 실패.',
                                           bootpay_receipt_id=payment.receipt_id)

            # 결제취소실패
            payment.status = -20
            payment.save()
        return Response(status=status.HTTP_200_OK)  # hmm..

    @action(methods=['post'], detail=False)
    def error(self, request):
        """
        결제 중 에러 발생 시 client 에서 호출하는 api 입니다.
        상품 상태를 초기화 합니다.
        api: POST api/v1/payment/error/
        :param request: order_id(payment id와 동일)
        """

        payment = Payment.objects.get(pk=request.data.get('order_id'))
        bootpay = self.get_access_token()
        result = bootpay.cancel(payment.receipt_id, '{}'.format(payment.price), '디오디', '결제 과정 중 에러발생. 디오디로 문의해주세요.')
        serializer = PaymentCancelSerialzier(payment, data=result['data'])

        # 오류로 인한 결제실패
        payment.status = -1
        payment.save()

        if serializer.is_valid():
            serializer.save()

            # trade : bootpay 환불 완료
            Product.objects.filter(project__payment=payment).update(status=2)  # 결제되었다가 취소이므로 환불.

            # payment : 결제 취소 완료
            payment.status = 20
            payment.save()
            PaymentErrorLog.objects.create(user=request.user, temp_payment=payment,
                                           description='(환불완료)[결제 과정 중 에러] 환불 완료.',
                                           bootpay_receipt_id=payment.receipt_id)

            return Response({'detail': 'canceled'}, status=status.HTTP_200_OK)
        else:
            PaymentErrorLog.objects.create(user=request.user, temp_payment=payment,
                                           description='(환불안됨)[결제 과정 중 에러] 결제 진행 중 에러발생. 결제취소 실패.',
                                           bootpay_receipt_id=payment.receipt_id)
            # 결제취소실패
            payment.status = -20
            payment.save()
        return Response(status=status.HTTP_200_OK)  # hmm..

    def check_owner(self):
        if self.project.owner != self.user:
            raise exceptions.NotAcceptable(detail='결제자 정보가 다릅니다.')

    def check_price(self):
        price = sum(list(self.products.values_list('price', flat=True)))
        if int(self.data['price']) != int(price):
            raise exceptions.NotAcceptable(detail='가격을 확인해주시길 바랍니다.')

    def check_product_filled(self):
        # 추후 기프티콘을 채운다면 사용할 예정
        # 만약 자동발송이라면 사용 안함
        pass

    def create_payment(self):
        name = self._set_products_name()
        price = self.data['price']
        self.payment = Payment.objects.create(user=self.user,
                                              name=name,
                                              price=price,
                                              project=self.project,
                                              pg='payapp')

    def _set_products_name(self):
        item_names = list(self.products.values_list('item__name', flat=True))
        name_counts = {i: item_names.count(i) for i in item_names}
        name = ''
        for i, val in enumerate(name_counts):
            if i < len(name_counts) - 1:
                name += '{} x{}, '.format(val, name_counts[val])
            else:
                name += '{} x{}'.format(val, name_counts[val])
        return name






