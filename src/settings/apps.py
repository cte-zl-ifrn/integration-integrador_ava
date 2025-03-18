from sc4py.env import env, env_as_list, env_as_bool
import datetime

APP_VERSION = "1.1.014"

LAST_STARTUP = int(datetime.datetime.timestamp(datetime.datetime.now()) * 1000)

SHOW_SUPPORT_FORM = env_as_bool("SHOW_SUPPORT_FORM", True)
SHOW_SUPPORT_CHAT = env_as_bool("SHOW_SUPPORT_CHAT", True)


# Apps
MY_APPS = env_as_list(
    "MY_APPS",
    [
        "integrador",
        "security",
        "health",
    ],
)

THIRD_APPS = env_as_list(
    "THIRD_APPS",
    [
        # 'markdownx',
        "import_export",
        "simple_history",
        "safedelete",
        "sass_processor",
        "djrichtextfield",
        "django_json_widget",
        # "django_admin_json_editor",
        # "corsheaders",
        "adminlte3",
        # "adminlte3/admin",
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
    ],
)
HACK_APPS = env_as_list("HACK_APPS", [])
INSTALLED_APPS = MY_APPS + THIRD_APPS + DJANGO_APPS + HACK_APPS
