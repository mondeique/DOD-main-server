from dod.settings.base import *

DEVEL = True
PROD = False
STAG = False

SETTING_DEV_DIC = load_credential("develop")
SECRET_KEY = SETTING_DEV_DIC['SECRET_KEY']
DEBUG = True

ALLOWED_HOSTS = ['*']


# AUTH USER
AUTH_USER_MODEL = 'accounts.User'

DATABASES = {
    'default': SETTING_DEV_DIC["default"],
}

CORS_ORIGIN_ALLOW_ALL = True
