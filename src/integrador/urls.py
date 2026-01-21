from django.urls import path
from django.conf import settings
from django.views.generic import RedirectView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .apps import IntegradorConfig
from .views import sync_up_enrolments, sync_down_grades


app_name = IntegradorConfig.name


# Removendo decoradores csrf_exempt aqui pois são APIs públicas (autenticadas por token)
urlpatterns = [
    path(f"enviar_diarios/", sync_up_enrolments, name="api_sync_up_enrolments"),
    path(f"baixar_notas/", sync_down_grades, name="api_sync_down_grades"),
]
