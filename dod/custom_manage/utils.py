import datetime
import random
import string

from core.sms.utils import LMSV1Manager
from projects.models import Project
from respondent.models import AlertAgreeRespondent


def generate_random_key(length=10):
    return ''.join(random.choices(string.digits + string.ascii_letters, k=length))


def send_alert_agree_sms(phone=None):
    if phone:
        phone = str(phone)
        respondent = AlertAgreeRespondent.objects.create(phone=phone, key=generate_random_key())
        message = set_message(respondent)
        lms_manager = LMSV1Manager()
        lms_manager.alert_agree_content(message)
        if lms_manager.send_lms(phone=respondent.phone):
            respondent.send = True
            respondent.save()
        print('test END')
    else:
        yesterday = datetime.datetime.now().date() - datetime.timedelta(days=1)
        projects = Project.objects.filter(dead_at__gte=yesterday, is_active=True, kind=Project.NORMAL)
        respondent_list = list(set(list(projects.values_list('respondents__phone_confirm__phone', flat=True))))
        sent_list = list(AlertAgreeRespondent.objects.all().values_list('phone', flat=True))
        new_respondent_list = list(set(respondent_list)-set(sent_list))
        new_respondent_list = list(filter(bool, new_respondent_list))
        alert_respondent_list = [AlertAgreeRespondent(phone=i, key=generate_random_key()) for i in new_respondent_list]
        AlertAgreeRespondent.objects.bulk_create(alert_respondent_list)

        count = 0
        for respondent in AlertAgreeRespondent.objects.filter(send=False):
            message = set_message(respondent)
            lms_manager = LMSV1Manager()
            lms_manager.alert_agree_content(message)
            if lms_manager.send_lms(phone=respondent.phone):
                respondent.send = True
                respondent.save()

            print('process: {}'.format(count))
            count = count + 1

        print('SEND FIN')


def set_message(respondent):
    url = 'https://d-o-d.io/alim/{}/'.format(respondent.key)
    # url = 'http://3.36.156.224:8010/alim/{}/'.format(respondent.key)
    message = '\n안녕하세요 실시간 추첨서비스 디오디입니다.\n\n' \
              '추첨에 사용하셨던 전화번호 파기함을 안내드리며,\n' \
              '다음 실시간 추첨 설문이 올라올 때 알림을 받고 싶으시다면 ' \
              '아래 링크로 신청해주세요.\n' \
              '{}\n\n' \
              '※ 해당 안내문자 이후 전화번호는 파기됩니다.'.format(url)
    return message
