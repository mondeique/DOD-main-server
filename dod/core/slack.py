import json
import requests

from .loader import load_credential


def deposit_success_slack_message(message):
    incomming_url = load_credential("slack", "")['DepositSuccessUrl']
    post_data = {"text": '{}'.format(message)}
    data = json.dumps(post_data)
    headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
    response = requests.post(incomming_url, headers=headers, data=data)
    return None

def deposit_temp_slack_message(message):
    incomming_url = load_credential("slack", "")['DepositTempUrl']
    post_data = {"text": '{}'.format(message)}
    data = json.dumps(post_data)
    headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
    response = requests.post(incomming_url, headers=headers, data=data)
    return None

def mms_failed_slack_message(message):
    incomming_url = load_credential("slack", "")['MMSFailedNoticeUrl']
    post_data = {"text": '{}'.format(message)}
    data = json.dumps(post_data)
    headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
    response = requests.post(incomming_url, headers=headers, data=data)
    return None


