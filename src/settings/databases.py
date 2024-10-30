# -*- coding: utf-8 -*-
from sc4py.env import env

# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": env("POSTGRES_ENGINE", "django.db.backends.postgresql"),
        "HOST": env("POSTGRES_HOST", "db"),
        "PORT": env("POSTGRES_PORT", "5432"),
        "NAME": env("POSTGRES_DATABASE", "integrador"),
        "USER": env("POSTGRES_USER", "postgres"),
        "PASSWORD": env("POSTGRES_PASSWORD", "postgres"),
        "OPTIONS": {"options": env("POSTGRES_OPTIONS", "")},
    },
}

# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
