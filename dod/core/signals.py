from django.db.models.signals import post_save
from django.dispatch import receiver

from core.slack import mms_failed_slack_message
from core.sms.utils import MMSV1Manager
from logs.models import MMSSendLog


@receiver(post_save, sender=MMSSendLog)
def slack_notice_failed_send_mms(sender, **kwargs):
    mms_send_log = kwargs['instance']
    if not mms_send_log.resend:
        msg = "[MMS발송실패]\n전화번호: {}\n상품명: {}\n유효기간: {}\n\n재발송은 Staff Page의 MMS Log에서 가능합니다."\
            .format(mms_send_log.phone, mms_send_log.item_name, mms_send_log.due_date)
        try:
            mms_failed_slack_message(msg)
        except:
            pass
    else:
        if mms_send_log.due_date:
            phone = mms_send_log.phone
            brand = mms_send_log.brand
            item_name = mms_send_log.item_name
            item_url = mms_send_log.item_url
            due_date = mms_send_log.due_date
            mms_manager = MMSV1Manager()
            mms_manager.set_content(brand, item_name, due_date)
            success, code = mms_manager.send_mms(phone=phone, image_url=item_url)
            if not success:
                MMSSendLog.objects.create(code="Staff 재발송도 실패", phone=phone, item_name=item_name, item_url=item_url, due_date=due_date)
        else:
            # UPDATED 20210725 custom upload resend
            phone = mms_send_log.phone
            item_url = mms_send_log.item_url
            mms_manager = MMSV1Manager()
            mms_manager.set_custom_upload_content()
            success, code = mms_manager.send_mms(phone=phone, image_url=item_url)
            if not success:
                MMSSendLog.objects.create(code="Staff 재발송도 실패", phone=phone, item_name='', item_url=item_url)
