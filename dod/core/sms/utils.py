import os
import string
import time

import random
import json
from accounts.models import PhoneConfirm
from core.sms.signature import time_stamp, make_signature
from respondent.models import RespondentPhoneConfirm
from ..loader import load_credential
import requests
import base64
from PIL import Image

# class SMSManager():
#     """
#     DEPRECATED
#     """
#     serviceId = load_credential("serviceId")
#     access_key = load_credential("access_key")
#     secret_key = load_credential("secret_key")
#     _from = load_credential("_from")  # 발신번호
#     url = "https://api-sens.ncloud.com/v1/sms/services/{}/messages".format(serviceId)
#     headers = {
#         'Content-Type': 'application/json; charset=utf-8',
#         'x-ncp-auth-key': access_key,
#         'x-ncp-service-secret': secret_key,
#     }
#
#     def __init__(self):
#         self.confirm_key = ""
#         self.temp_key = uuid.uuid4()
#         self.body = {
#             "type": "SMS",
#             "countryCode": "82",
#             "from": self._from,
#             "to": [],
#             "subject": "",
#             "content": ""
#         }
#
#     def create_instance(self, phone, kind):
#         phone_confirm = PhoneConfirm.objects.create(
#             phone=phone,
#             confirm_key=self.confirm_key,
#             temp_key=self.temp_key,
#             kinds=kind
#         )
#         return phone_confirm
#
#     def generate_random_key(self):
#         return ''.join(random.choices(string.digits, k=4))
#
#     def set_certification_number(self):
#         self.confirm_key = self.generate_random_key()
#
#     def set_content(self):
#         self.set_certification_number()
#         self.body['content'] = "[DOD 디오디] 사용자의 인증 코드는 {}입니다.".format(self.confirm_key)
#
#     def send_sms(self, phone):
#         self.body['to'] = [phone]
#         request = requests.post(self.url, headers=self.headers, data=json.dumps(self.body, ensure_ascii=False).encode('utf-8'))
#         print(request.status_code)
#         if request.status_code == 202:
#             return True
#         else:
#             return False


class SMSV2Manager():
    """
    인증번호 발송(ncloud 사용)을 위한 class 입니다.
    v2 로 업데이트 하였습니다. 2020.06
    """
    def __init__(self):
        self.confirm_key = ""
        self.body = {
            "type": "SMS",
            "contentType": "COMM",
            "from": load_credential("sms")["_from"], # 발신번호
            "content": "",  # 기본 메시지 내용
            "messages": [{"to": ""}],
        }

    def generate_random_key(self):
        return ''.join(random.choices(string.digits, k=4))

    def set_confirm_key(self):
        self.confirm_key = self.generate_random_key()

    def create_instance(self, phone, kinds):
        phone_confirm = PhoneConfirm.objects.create(
            phone=phone,
            confirm_key=self.confirm_key,
            kinds=kinds
        )
        return phone_confirm

    def set_content(self):
        self.set_confirm_key()
        self.body['content'] = "[디오디] 본인확인을 위해 인증번호 {}를 입력해 주세요.".format(self.confirm_key)

    def create_respondent_send_instance(self, phone):
        respondent_phone_confirm = RespondentPhoneConfirm.objects.create(
            phone=phone,
            confirm_key=self.confirm_key,
        )
        return respondent_phone_confirm

    def set_respondent_content(self):
        self.set_confirm_key()
        self.body['content'] = "[디오디] 당첨확인을 위해 인증번호 {}를 입력해 주세요.".format(self.confirm_key)

    def send_sms(self, phone):
        sms_dic = load_credential("sms")
        access_key = sms_dic['access_key']
        url = "https://sens.apigw.ntruss.com"
        uri = "/sms/v2/services/" + sms_dic['serviceId'] + "/messages"
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
        request = requests.post(api_url, headers=headers, data=json.dumps(self.body))
        if request.status_code == 202:
            return True
        else:
            return False


class MMSV1Manager():
    """
    당첨 이미지 발송(ncloud 사용)을 위한 class 입니다.
    SMS Manager 와 같은 API 를 사용하지만 MMS 로 인해 추가로 들어가는 부분 있음
    """

    def __init__(self):
        self.body = {
            "type": "MMS",
            "contentType": "COMM",
            "from": load_credential("sms")["_from"], # 발신번호
            "content": "당첨을 축하합니다.",  # 기본 메시지 내용
            "messages": [{"to": ""}],
            "files": [{"name": "string", "body": "string"}]
        }

    def set_content(self, product_name):
        self.body['content'] = "[디오디] 당첨 안내 \n 안녕하세요 디오디입니다. \n 추첨결과 {}에 당첨되셨습니다. \n 축하드립니다!! \n" \
                               "※ 유효기간을 확인하고 사용 해 주세요! \n\n ▷ 문의하기 \n - 고객센터 : 02-334-1133 \n 09:00 ~ 20:00 " \
                               "(주말&공휴일 포함) ".format(product_name)

    def send_mms(self, phone, image_url):
        sms_dic = load_credential("sms")
        access_key = sms_dic['access_key']
        url = "https://sens.apigw.ntruss.com"
        uri = "/sms/v2/services/" + sms_dic['serviceId'] + "/messages"
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

        # download gift.jpg from url
        os.system("curl " + image_url + " > gift.jpg")

        with open("gift.jpg", "rb") as image_file:
            data = base64.b64encode(image_file.read())

        self.body['messages'][0]['to'] = phone
        self.body['files'][0]['name'] = "gift.jpg"
        self.body['files'][0]['body'] = data.decode('utf-8')
        request = requests.post(api_url, headers=headers, data=json.dumps(self.body))
        if request.status_code == 202:
            return True
        else:
            return False