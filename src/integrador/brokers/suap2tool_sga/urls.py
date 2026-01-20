from django.urls import path
from django.conf import settings
from django.views.generic import RedirectView
from .apps import IntegradorConfig
from .views import suap_enviar_diarios, suap_baixar_notas


app_name = IntegradorConfig.name


urlpatterns = [
]
