from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny

from products.models import Item
from products.serializers import ItemRetrieveSerializer


class ItemListViewSet(mixins.ListModelMixin,
                             viewsets.GenericViewSet):
    queryset = Item.objects.filter(is_active=True).select_related('brand')
    permission_classes = [AllowAny]
    serializer_class = ItemRetrieveSerializer
    pagination_class = None

