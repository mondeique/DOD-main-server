from django.urls import path, include
from rest_framework.routers import DefaultRouter
from notice.views import DodExplanationAPIView, ThirdPartyMenuListAPIView

app_name = 'notice'


router = DefaultRouter()
router.register('dod-explanation', DodExplanationAPIView, basename='dod-explanation')
router.register('third-party-menus', ThirdPartyMenuListAPIView, basename='third-party-menus')

urlpatterns = [
    path('', include(router.urls)),
]