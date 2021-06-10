import string
import time

import random
import json
from accounts.models import PhoneConfirm
from core.sms.signature import time_stamp, make_signature
from respondent.models import RespondentPhoneConfirm
from ..loader import load_credential
import requests
import uuid


class ALIMV1Manager():
    """
    알림톡 인증번호 발송(ncloud 사용)을 위한 class 입니다.
    """
    def __init__(self):
        self.confirm_key = ""
        self.body = {
                        "plusFriendId": "dod_gift",
                        "templateCode": "string",
                        "messages": [
                            {
                                "countryCode": "82",
                                "to": "",
                                "title": "",
                                "content": "",
                            }
                        ]
                    }


    def send_alim(self, phone):
        alim_dic = load_credential("alim")
        access_key = alim_dic["access_key"]
        url = "https://sens.apigw.ntruss.com"
        uri = "/alimtalk/v2/services/" + alim_dic["serviceId"] + "/messages"
        api_url = url + uri
        timestamp = str(int(time.time() * 1000))
        string_to_sign = "POST " + uri + "\n" + timestamp + "\n" + access_key
        signature = make_signature(string_to_sign)

        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'x-ncp-apigw-timestamp': timestamp,
            'x-ncp-iam-access-key': access_key,
            'x-ncp-apigw-signature-v2': signature
        }

        self.body['messages'][0]['to'] = phone
        # TODO: message content template 규격 맞춰야함
        self.body['messages'][0]['content'] = phone

        request = requests.post(api_url, headers=headers, data=json.dumps(self.body))
        if request.status_code == 202:
            return True
        else:
            return False
