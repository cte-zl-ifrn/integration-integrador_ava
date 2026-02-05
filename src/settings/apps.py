from sc4py.env import env, env_as_list, env_as_bool

THIRD_APPS = env_as_list("THIRD_APPS", ["import_export", "simple_history", "sass_processor", "django_json_widget", "django_extensions", "django_rule_engine"])
DJANGO_APPS = [f"django.contrib.{x}" for x in ["admin", "auth", "contenttypes", "sessions", "messages", "staticfiles", "humanize"]]
MY_APPS = env_as_list("MY_APPS", ["cohort", "integrador", "security", "dashboard", "base", "dsgovbr", "health"])
HACK_APPS = env_as_list("HACK_APPS", ["hacks"])
INSTALLED_APPS = MY_APPS + THIRD_APPS + DJANGO_APPS + HACK_APPS
