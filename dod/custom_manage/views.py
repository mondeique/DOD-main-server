import datetime
import random

from django.shortcuts import render
from django.http import HttpResponseRedirect
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from rest_framework.views import APIView

from accounts.models import User
from core.slack import lambda_monitoring_slack_message
from core.sms.utils import MMSV1Manager, SMSV2Manager
from core.tools import get_client_ip
from logs.models import MMSSendLog
from products.models import Reward
from projects.models import Project, ProjectMonitoringLog
from respondent.models import RespondentPhoneConfirm
from .forms import PostForm


def reset_pw(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            pw = form.cleaned_data['password']
            user = User.objects.get(phone=phone)
            user.set_password(pw)
            user.save()
            return HttpResponseRedirect("/staff/")
    else:
        if request.user.is_anonymous:
            return HttpResponseRedirect("/staff/")
        form = PostForm()
    return render(request, 'staff_pw_change.html',{
        'form': form,
    })


class AutoSendLeftMMSAPIView(APIView):
    # permission_classes = [IsAuthenticated,]

    def get(self, request, *args, **kwargs):
        if 'python-requests' not in request.META.get('HTTP_USER_AGENT', ""):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        now = datetime.datetime.now()  # every 09:10
        monitoring_logs = ProjectMonitoringLog.objects.filter(draw_again=False).filter(project__dead_at__lte=now). \
            filter(project__is_active=True, project__status=True)
        project_qs = Project.objects.filter(monitoring_logs__in=monitoring_logs) \
            .prefetch_related('products',
                              'products__rewards',
                              'respondents',
                              'respondents__phone_confirm',
                              'monitoring_logs')
        total_left_rewards = 0
        total_succeed_mms = 0
        for project in project_qs:
            left_rewards = Reward.objects.filter(winner_id__isnull=True, product__project=project)
            if left_rewards.exists():
                left_count = left_rewards.count()
                total_left_rewards = total_left_rewards + left_count
                phone_list = list(project.respondents.filter(is_win=False).
                                  values_list('phone_confirm__phone', 'id'))
                try:
                    new_winners = random.sample(phone_list, left_count)
                    for i, reward in enumerate(left_rewards):
                        winner = new_winners[i][0]  # phone
                        brand = reward.product.item.brand.name
                        item_name = reward.product.item.name
                        item_url = reward.reward_img.url
                        due_date = reward.due_date
                        if type(item_url) is tuple:
                            item_url = ''.join(item_url)
                        if type(item_name) is tuple:
                            item_name = ''.join(item_name)

                        mms_manager = MMSV1Manager()
                        mms_manager.set_monitored_content(brand, item_name, due_date)
                        success, code = mms_manager.send_mms(phone=winner, image_url=item_url)
                        if not success:
                            MMSSendLog.objects.create(code=code, phone=winner, item_name=item_name, item_url=item_url,
                                                      due_date=due_date, brand=brand)
                        else:
                            total_succeed_mms = total_succeed_mms + 1
                        reward.winner_id = new_winners[i][1]
                        reward.save()
                except:
                    pass
        msg = '\n[재추첨 로그]\n' \
              '현재시간: {}\n' \
              '재전송 프로젝트: {}개\n' \
              '재전송 설문자수: {}명\n' \
              '재전송 문자개수: {}개\n' \
              '---------------------'.format(datetime.datetime.now(), project_qs.count(),
                                             total_left_rewards, total_succeed_mms)
        lambda_monitoring_slack_message(msg)
        monitoring_logs.update(draw_again=True)
        return Response(status=status.HTTP_200_OK)


class ProjectDeadLinkNotification(APIView):

    def get(self, request, *args, **kwargs):
        if 'python-requests' not in request.META.get('HTTP_USER_AGENT', ""):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        now = datetime.datetime.now()  # every 16:10
        buffer_day = now + datetime.timedelta(hours=12)  # 그날 저녁에 끝나는 project들

        monitoring_logs = ProjectMonitoringLog.objects.filter(dead_line_notice=False). \
            filter(project__dead_at__gte=now, project__dead_at__lte=buffer_day). \
            filter(project__is_active=True, project__status=True)
        project_qs = Project.objects.filter(monitoring_logs__in=monitoring_logs) \
            .prefetch_related('respondents', 'respondents__phone_confirm')
        total_succeed_sms = 0
        for project in project_qs:
            phone = project.owner.phone

            sms_manager = SMSV2Manager()
            sms_manager.project_deadline_notice_content()
            sms_manager.send_sms(phone=phone)
            total_succeed_sms = total_succeed_sms + 1

        msg = '\n[추첨링크 마감 안내 로그]\n' \
              '현재시간: {}\n' \
              '발송 유저 수: {}명\n' \
              '전송 문자개수: {}개\n' \
              '---------------------'.format(datetime.datetime.now(), project_qs.count(), total_succeed_sms)
        lambda_monitoring_slack_message(msg)
        monitoring_logs.update(dead_line_notice=True)

        return Response(status=status.HTTP_200_OK)


class RespondentCheckMonitoring(APIView):

    def post(self, request, *args, **kwargs):
        token = request.data.get('token', '')
        if token != 'ttlcT3WNbqEQuwE424Tp8nxD':
            return Response(status=status.HTTP_400_BAD_REQUEST)
        staff_phone_list = list(User.objects.filter(is_staff=True).values_list('phone', flat=True))
        today = datetime.date.today()
        now = datetime.datetime.now()
        now = now.strftime('%Y년 %m월 %d일 %H:%M:%S')
        respondents = RespondentPhoneConfirm.objects.filter(is_confirmed=True).exclude(phone__in=staff_phone_list).prefetch_related('respondent')
        today_respondents = respondents.filter(created_at__gt=today)
        today_respondents_winner = today_respondents.filter(respondent__is_win=True)
        today_respondents_failed = today_respondents.filter(respondent__is_win=False)
        msg = "\n\n 응답자 현황을 알려줄게\n" \
              "<{}시 기준>\n\n" \
              "[오늘]" \
              "응답: {}명\n" \
              "당첨: {}명\n" \
              "탈락: {}명\n" \
              "\n" \
              "[누적]" \
              '응답: {}명\n'.format(now, today_respondents.count(), today_respondents_winner.count(), today_respondents_failed.count(), respondents.count())
        lambda_monitoring_slack_message(msg)
        return Response(status=status.HTTP_200_OK)

