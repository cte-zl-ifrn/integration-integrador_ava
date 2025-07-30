# -*- coding: utf-8 -*-
from sc4py.env import env

# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": env("POSTGRES_ENGINE", 'django_tenants.postgresql_backend'),
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



# https://django-tenants.readthedocs.io/en/latest/install.html#basic-settings
TENANT_MODEL = "gestao.Cliente" # tenants
TENANT_DOMAIN_MODEL = "gestao.Dominio" # tenants
PUBLIC_SCHEMA_NAME = "public" # tenants
DATABASE_ROUTERS = ('django_tenants.routers.TenantSyncRouter',) # tenants

