import logging

from integrador.brokers.base import BaseBroker
from integrador.models import Solicitacao

logger = logging.getLogger(__name__)


class Sga2ToolSgaBroker(BaseBroker):
    def sync_up_enrolments(self, solicitacao: Solicitacao) -> dict:
        raise NotImplementedError("Ainda não implementado.")

    def baixar_notas(self, solicitacao: Solicitacao) -> dict:
        raise NotImplementedError("Ainda não implementado.")
