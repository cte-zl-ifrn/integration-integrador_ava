# -*- coding: utf-8 -*-
from pathlib import Path
from sc4py.env import env, env_as_bool

# https://docs.djangoproject.com/en/5.0/topics/i18n/


LANGUAGE_CODE = env("DJANGO_LANGUAGE_CODE", "pt-br")
TIME_ZONE = env("DJANGO_TIME_ZONE", "America/Fortaleza")
USE_I18N = env_as_bool("DJANGO_USE_I18N", True)
USE_L10N = env_as_bool("DJANGO_USE_L10N", True)
USE_TZ = env_as_bool("DJANGO_USE_TZ", True)
USE_THOUSAND_SEPARATOR = env_as_bool("DJANGO_USE_THOUSAND_SEPARATOR", True)
