from sc4py.env import env, env_as_list, env_as_bool
import datetime

APP_LABEL = "Integrador AVA"
APP_VERSION = "1.1.025"
APP_LAST_STARTUP = int(datetime.datetime.timestamp(datetime.datetime.now()) * 1000)

SHOW_SUPPORT_FORM = env_as_bool("SHOW_SUPPORT_FORM", True)
SHOW_SUPPORT_CHAT = env_as_bool("SHOW_SUPPORT_CHAT", True)

THIRD_APPS = env_as_list(
    "THIRD_APPS", ["import_export", "simple_history", "sass_processor", "django_json_widget"]
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
MY_APPS = env_as_list("MY_APPS", ["base", "coorte", "edu", "health", "integrador", "security", "dsgovbr"])
def _dedupe_apps(apps_list):
    seen = set()
    out = []
    for a in apps_list:
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out

# `gestao` must not be present in tenant-installed apps
TENANT_APPS = THIRD_APPS + MY_APPS + DJANGO_APPS

# Shared apps are those not part of tenant apps (MY_APPS)
SHARED_APPS = THIRD_APPS + DJANGO_APPS + ["gestao"]

# montar INSTALLED_APPS garantindo ordem e sem duplicatas
def _dedupe_apps(apps_list):
    seen = set()
    out = []
    for a in apps_list:
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out

# Ensure `django_tenants` is loaded first and `gestao` remains in shared apps only.
INSTALLED_APPS = _dedupe_apps(["django_tenants", "gestao"] + MY_APPS + THIRD_APPS + DJANGO_APPS + HACK_APPS)
