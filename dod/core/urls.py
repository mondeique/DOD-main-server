from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.views import SMSViewSet

app_name = 'core'

router = DefaultRouter()
router.register('sms', SMSViewSet, basename='sms')

urlpatterns = [
    path('', include(router.urls)),
]