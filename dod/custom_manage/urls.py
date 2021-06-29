from django.urls import path, include

from custom_manage.views import reset_pw, AutoSendLeftMMSAPIView, ProjectDeadLinkNotification

app_name = 'custom_manage'


urlpatterns = [
    path('reset_pw/', reset_pw),
    path('auto_send_mms/', AutoSendLeftMMSAPIView.as_view()),
    path('deadline_send_sms/', ProjectDeadLinkNotification.as_view()),
]