from django.urls import path, include
from rest_framework.routers import DefaultRouter
from notice.views import DodExplanationAPIView

app_name = 'notice'


router = DefaultRouter()
router.register('dod-explanation', DodExplanationAPIView, basename='dod-explanation')

urlpatterns = [
    path('', include(router.urls)),
]