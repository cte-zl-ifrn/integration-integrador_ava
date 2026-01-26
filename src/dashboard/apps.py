from tabnanny import verbose
from django.apps import AppConfig


class DashboardConfig(AppConfig):
    name: str = "dashboard"
    verbose_name: str = "Dashboard"
    icon: str = "fa fa-dashboard"
    def ready(self):
        """
        Executado quando o Django está pronto.
        Aqui registramos o dashboard customizado no admin.
        """
        from django.contrib import admin
        from .admin_views import admin_index_dashboard
        
        # Registra a view personalizada como página inicial do admin
        admin.site.index = admin_index_dashboard