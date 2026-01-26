from sc4py.env import env, env_as_list, env_as_bool
import datetime

PROJECT_COMPANY = "IFRN"
PROJECT_TITLE = "Integrador AVA"
PROJECT_SUBTITLE = "Sistema de integração de Ambientes Virtuais de Aprendizagem"
PROJECT_VERSION = "1.1.033"
PROJECT_LAST_STARTUP = int(datetime.datetime.timestamp(datetime.datetime.now()) * 1000)

SHOW_SUPPORT_FORM = env_as_bool("SHOW_SUPPORT_FORM", True)
SHOW_SUPPORT_CHAT = env_as_bool("SHOW_SUPPORT_CHAT", True)

THIRD_APPS = env_as_list("THIRD_APPS", ["import_export", "simple_history", "sass_processor", "django_json_widget", "django_extensions", "django_rule_engine"])
DJANGO_APPS = [f"django.contrib.{x}" for x in ["admin", "auth", "contenttypes", "sessions", "messages", "staticfiles", "humanize"]]
MY_APPS = env_as_list("MY_APPS", ["base", "coorte", "edu", "health", "integrador", "security", "dsgovbr"])
try:
    import dsgovbr
except ImportError:
    MY_APPS.remove("dsgovbr")
HACK_APPS = env_as_list("HACK_APPS", ["hacks"])
INSTALLED_APPS = MY_APPS + THIRD_APPS + DJANGO_APPS + HACK_APPS
