import os

ENV_SETTINGS_MODE = os.getenv('SETTINGS_MODE', '')

if ENV_SETTINGS_MODE == 'prod':
    print('0-----')
    from dod.settings.production import *
elif ENV_SETTINGS_MODE == 'stag':
    from dod.settings.stagging import *
elif ENV_SETTINGS_MODE == 'devel':
    from dod.settings.develop import *
