from sc4py.env import env, env_as_list, env_as_bool
import datetime

APP_VERSION = "1.1.018"

LAST_STARTUP = int(datetime.datetime.timestamp(datetime.datetime.now()) * 1000)

SHOW_SUPPORT_FORM = env_as_bool("SHOW_SUPPORT_FORM", True)
SHOW_SUPPORT_CHAT = env_as_bool("SHOW_SUPPORT_CHAT", True)


MY_APPS = env_as_list(
    "MY_APPS",
    [
        'base',
        'coorte',
        'edu',
        "health",
        'integrador',
        "security",
    ],
)

THIRD_APPS = env_as_list(
    "THIRD_APPS",
    [
        "django_tenants", # tenants
        "import_export",
        "simple_history",
        "sass_processor",
        # "djrichtextfield",
        "django_json_widget",
    ],
)

try:
    import django_extensions

    THIRD_APPS.append("django_extensions")
except ModuleNotFoundError:
    pass


DJANGO_APPS = env_as_list(
    "DJANGO_APPS",
    [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "django.contrib.humanize",
    ],
)
HACK_APPS = env_as_list("HACK_APPS", ["hacks"])

SHARED_APPS = MY_APPS + THIRD_APPS + DJANGO_APPS + HACK_APPS
TENANT_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
]
INSTALLED_APPS = SHARED_APPS + [a for a in TENANT_APPS if a not in SHARED_APPS]
