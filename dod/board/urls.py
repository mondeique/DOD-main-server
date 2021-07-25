from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BoardViewSet, BoardDODCheckAPIView

app_name = 'boards'


router = DefaultRouter()
router.register('board', BoardViewSet, basename='board')

urlpatterns = [
    path('', include(router.urls)),
]