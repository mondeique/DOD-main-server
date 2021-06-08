from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from custom_manage.sites import staff_panel
from products.models import Brand, Item, Product


class BrandStaffAdmin(admin.ModelAdmin):
    list_display = ['name', 'pk', 'is_active', 'created_at']
    list_editable = ['is_active']


class ItemStaffAdmin(admin.ModelAdmin):
    list_display = ['name', 'pk', 'thumb_img', 'brand_name', 'price', 'origin_price', 'is_active', 'created_at']
    list_editable = ['is_active']

    def thumb_img(self, obj):
        if obj.thumbnail:
            return mark_safe('<img src="%s" width=120px "/>' % obj.thumbnail.url)
        return '-'

    def brand_name(self, obj):
        brand = obj.brand
        return brand.name


class ProductStaffAdmin(admin.ModelAdmin):
    list_display = ['pk', 'project', 'item', 'count', 'total_price', 'created_at']

    def total_price(self, obj):
        return obj.item.price * obj.count


staff_panel.register(Brand, BrandStaffAdmin)
staff_panel.register(Item, ItemStaffAdmin)
staff_panel.register(Product, ProductStaffAdmin)
