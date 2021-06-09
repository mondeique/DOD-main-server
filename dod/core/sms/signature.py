import hashlib
import hmac
import base64
import time
from ..loader import load_credential


def time_stamp():
    return str(int(time.time() * 1000))


def make_signature(string_to_sign):
    secret_key = bytes(load_credential('secret_key'), 'UTF-8')
    string = bytes(string_to_sign, 'UTF-8')
    string_hmac = hmac.new(secret_key, string, digestmod=hashlib.sha256).digest()
    string_base64 = base64.b64encode(string_hmac).decode('UTF-8')
    return string_base64
