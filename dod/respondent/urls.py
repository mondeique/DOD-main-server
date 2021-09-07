from django.urls import path, include
from rest_framework.routers import DefaultRouter

from respondent.views import ClientRefererProjectValidateCheckViewSet, LotteryAnnouncementViewSet

app_name = 'respondent'


router = DefaultRouter()
router.register('check', ClientRefererProjectValidateCheckViewSet, basename='check')


urlpatterns = [
    path('', include(router.urls))
]