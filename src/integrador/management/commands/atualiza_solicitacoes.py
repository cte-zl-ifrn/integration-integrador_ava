# painel/management/commands/init_local_data.py
from django.core.management.base import BaseCommand
from django.conf import settings
from integrador.models import Solicitacao

class Command(BaseCommand):
    help = "Atualiza os registros de Solicitação para definir campos novos como nulos."

    def handle(self, *args, **options):
        while Solicitacao.objects.filter(diario_codigo__isnull=True).exists():
            for solicitacao in Solicitacao.objects.filter(diario_codigo__isnull=True).order_by("id")[0:1000]:
                solicitacao.ambiente = None
                solicitacao.campus_sigla = None
                solicitacao.diario_id = None
                solicitacao.diario_codigo = None
                solicitacao.tipo = None
                solicitacao.save()
