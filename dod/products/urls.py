from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ItemListViewSet

app_name = 'products'


router = DefaultRouter()
router.register('products', ItemListViewSet, basename='products')

urlpatterns = [
    path('', include(router.urls)),
]