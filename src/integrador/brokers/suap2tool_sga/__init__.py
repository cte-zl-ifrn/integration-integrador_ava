import logging
from integrador.brokers.base import BaseBroker


logger = logging.getLogger(__name__)


class Suap2ToolSgaBroker(BaseBroker):

    def sync_up_enrolments(self):
        raise NotImplementedError("Ainda não implementado.")

    def sync_down_grades(self):
        raise NotImplementedError("Ainda não implementado.")
