from django.urls import path, include
from rest_framework.routers import DefaultRouter
from payment.views import DepositInfoAPIView, DepositSuccessAPIView, BootpayFeedbackAPIView ,PaymentViewSet

app_name = 'payment'


router = DefaultRouter()
router.register('deposit-info', DepositInfoAPIView, basename='deposit-info')
router.register('deposit-success', DepositSuccessAPIView, basename='deposit-info')
router.register('payment', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('bootpay_feedback/', BootpayFeedbackAPIView.as_view()),
]