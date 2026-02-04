import logging
from integrador.models import Solicitacao
from integrador.brokers.base import BaseBroker


logger = logging.getLogger(__name__)


class Sga2ToolSgaBroker(BaseBroker):

    def sync_up_enrolments(self, solicitacao: Solicitacao) -> dict:
        raise NotImplementedError("Ainda não implementado.")

    def baixar_notas(self, solicitacao: Solicitacao) -> dict:
        raise NotImplementedError("Ainda não implementado.")
