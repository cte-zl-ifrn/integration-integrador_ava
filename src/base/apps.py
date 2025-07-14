from django.apps import AppConfig


class BaseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "base"
    icon = "fa fa-home"
    verbose_name = "Gestão"
