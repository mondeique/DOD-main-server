from dod.settings.base import *

DEVEL = False
PROD = False
STAG = True

print('stag')
SETTING_STAG_DIC = load_credential("stagging")
SECRET_KEY = SETTING_STAG_DIC['SECRET_KEY']

DEBUG = True

ALLOWED_HOSTS = ['*']

# AUTH USER
AUTH_USER_MODEL = 'accounts.User'

DATABASES = {
    'default': SETTING_STAG_DIC["default"],
}

CORS_ORIGIN_ALLOW_ALL = True
