"""dod URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include

from core.views import SendMMSAPIView
from custom_manage.sites import superadmin_panel, staff_panel
from custom_manage.views import AutoSendLeftMMSAPIView
from django.conf import settings

from payment.views import pay_test
from respondent.views import RefererValidatorAPIView, home, test_send

urlpatterns = [
    path('admin/', admin.site.urls),
    path('superadmin/', superadmin_panel.urls),
    path('staff/', staff_panel.urls, name='staff'),

    path('accounts/v1/', include('accounts.urls')),
    path('api/v1/', include('projects.urls')),
    path('api/v1/', include('products.urls')),
    path('api/v1/', include('notice.urls')),
    path('api/v1/', include('payment.urls')),
    path('api/v1/', include('core.urls')),
    path('api/v1/', include('respondent.urls')),
    path('api/v1/', include('board.urls')),
    path('api/manage/', include('custom_manage.urls')),


    # path('api/send-mms/', SendMMSAPIView.as_view()),
    path('pay_test/', pay_test, name='paytest'),

    # test send
    path('즉시추첨', test_send, name='test-send'),

    # ckeditors
    path('ckeditor/', include('ckeditor_uploader.urls')),
]
if settings.DEVEL or settings.STAG:
    urlpatterns += [
        path('link/<slug:slug>/', RefererValidatorAPIView.as_view()),
    ]
if settings.PROD:
    urlpatterns += [
        path('checklink/<slug:slug>/', RefererValidatorAPIView.as_view()),
    ]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),

        # For django versions before 2.0:
        # url(r'^__debug__/', include(debug_toolbar.urls)),

    ]