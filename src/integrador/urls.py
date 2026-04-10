from django.urls import path
from .apps import IntegradorConfig
from .views import sync_up_enrolments, sync_down_grades


app_name = IntegradorConfig.name


# Removendo decoradores csrf_exempt aqui pois são APIs públicas (autenticadas por token)
urlpatterns = [
    path("api/enviar_diarios/", sync_up_enrolments, name="api_sync_up_enrolments"),
    path("api/baixar_notas/", sync_down_grades, name="api_sync_down_grades"),
]
