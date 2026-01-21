"""API URLs for rule validation."""

from django.urls import path
from .views import validate_rule

urlpatterns = [
    path('validate-rule/', validate_rule, name='validate_rule'),
]
