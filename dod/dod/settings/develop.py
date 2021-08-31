from dod.settings.base import *

DEVEL = True
PROD = False
STAG = False

SETTING_DEV_DIC = load_credential("develop")
SECRET_KEY = SETTING_DEV_DIC['SECRET_KEY']
DEBUG = True

ALLOWED_HOSTS = ['*']
CORS_ORIGIN_WHITELIST = (
    'https://dod-beta.com',
    'https://d-o-d.io',
    'http://docs.gift',
    'http://172.30.1.26:3000'  # for local production db test
)
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# AUTH USER
AUTH_USER_MODEL = 'accounts.User'

DATABASES = {
    'default': SETTING_DEV_DIC["default"],
}

CORS_ORIGIN_ALLOW_ALL = True
