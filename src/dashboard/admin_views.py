"""
View personalizada para o dashboard de administração.
Integra dados de múltiplos modelos do integrador.
"""
import logging

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from dashboard.storage import DashboardStorage

logger = logging.getLogger(__name__)


@staff_member_required
def admin_index_dashboard(request):
    """
    Dashboard personalizado para a página inicial do admin.
    Agrega dados de ambientes e solicitações de integração.
    """
    storage = DashboardStorage()
    context = storage.get_context()

    # Adicionar histórico de ações do usuário
    try:
        log_entries = LogEntry.objects.filter(user=request.user).select_related('user').order_by('-action_time')
    except Exception:
        log_entries = []

    context['log_entries'] = log_entries
    
    # Adicionar available_apps ao contexto (necessário para o menu lateral)
    app_list = admin.site.get_app_list(request)
    context['available_apps'] = app_list

    return render(request, 'admin/index.html', context)
