"""Django app configuration for django_rule_engine."""

from django.apps import AppConfig


class DjangoRuleEngineConfig(AppConfig):
    """Configuration for Django rule-engine app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_rule_engine'
    verbose_name = 'Django Rule Engine'
