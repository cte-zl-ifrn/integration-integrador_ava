from django.urls import path
from django.conf import settings
from django.views.generic import RedirectView
from .apps import IntegradorConfig
from .views import sync_up_enrolments, sync_down_grades


app_name = IntegradorConfig.name


urlpatterns = [
    path("", RedirectView.as_view(url=f"/{settings.ROOT_URL_PATH}/admin/")),
    path("enviar_diarios/", sync_up_enrolments, name="api_sync_up_enrolments"),
    path("baixar_notas/", sync_down_grades, name="api_sync_down_grades"),
]
