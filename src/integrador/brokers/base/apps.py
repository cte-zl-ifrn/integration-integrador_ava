from django.apps import AppConfig


class BaseBrokerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "basebroker"
    icon = "fa fa-home"
