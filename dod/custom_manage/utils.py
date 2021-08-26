import datetime

from accounts.models import User
from core.sms.utils import SMSV2Manager
from projects.models import Project
from respondent.models import AlertAgreeRespondent


def send_alert_agree_sms(phone=None):
    if phone:
        phone = str(phone)
        respondent = AlertAgreeRespondent.objects.create(phone=phone)
        message = set_message(respondent)
        sms_manager = SMSV2Manager()
        sms_manager.alert_agree_content(message)
        if sms_manager.send_sms(phone=respondent.phone):
            respondent.send = True
            respondent.save()
        print('test END')
    else:
        yesterday = datetime.datetime.now().date() - datetime.timedelta(days=1)
        projects = Project.objects.filter(dead_at__gte=yesterday, is_active=True, kind=Project.NORMAL)
        respondent_list = list(set(list(projects.values_list('respondents__phone_confirm__phone', flat=True))))
        sent_list = list(AlertAgreeRespondent.objects.all().values_list('phone', flat=True))
        new_respondent_list = list(set(respondent_list)-set(sent_list))

        alert_respondent_list = [AlertAgreeRespondent(phone=i) for i in new_respondent_list]
        AlertAgreeRespondent.objects.bulk_create(alert_respondent_list)

        count = 0
        for respondent in AlertAgreeRespondent.objects.filter(send=False):
            message = set_message(respondent)
            sms_manager = SMSV2Manager()
            sms_manager.alert_agree_content(message)
            if sms_manager.send_sms(phone=respondent.phone):
                respondent.send = True
                respondent.save()

            print('process: {}'.format(count))
            count = count + 1

        print('SEND FIN')


def set_message(respondent):
    url = 'https://d-o-d.io/thanks/for/agree/{}/'.format(respondent.key)
    message = '[추첨번호 파기안내]\n' \
              '안녕하세요 실시간 추첨서비스 디오디입니다.\n\n' \
              '추첨에 사용하셨던 정보를 파기함을 안내드리며,\n' \
              '만약 다음 추첨이 올라올 때 가장먼저 알림을 받고 싶으시다면' \
              '아래 디오디 링크로 접속 해 주시면 감사하겠습니다:)\n' \
              '{}\n\n' \
              '※ 해당 안내문자 이후 전화번호는 파기됩니다.'.format(url)
    return message