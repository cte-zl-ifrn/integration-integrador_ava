# -*- coding: utf-8 -*-
from sc4py.env import env_as_bool

# Integrador
MIDDLEWARE = [
    # https://django-tenants.readthedocs.io/en/latest/install.html#basic-settings
    "django_tenants.middleware.main.TenantMainMiddleware", # tenants
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

