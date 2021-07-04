from django.db.models.signals import post_save
from django.dispatch import receiver

from core.slack import deposit_temp_slack_message
from core.sms.utils import SMSV2Manager
from payment.models import UserDepositLog


@receiver(post_save, sender=UserDepositLog)
def user_deposit_log_send_sms(sender, **kwargs):
    pass
    # deposit_log = kwargs['instance']
    # if deposit_log.confirm:
    #     try:
    #         sms_manager = SMSV2Manager()
    #         phone = deposit_log.project.owner.phone
    #         sms_manager.deposit_confirm_content()
    #         sms_manager.send_sms(phone=phone)
    #     except:
    #         pass
