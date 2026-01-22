import logging


logger = logging.getLogger(__name__)


class BaseBroker:

    def __init__(self, solicitacao):
        self.solicitacao = solicitacao

    @property
    def credentials(self) -> dict:
        c = {"Authentication": f"Token {self.solicitacao.ambiente.token}"}
        return c

    def get_coortes(self) -> list:
        return []

    def sync_up_enrolments(self) -> dict:
        raise NotImplementedError("Este método deve ser implementado pelas subclasses.")

    def sync_down_grades(self) -> dict:
        raise NotImplementedError("Este método deve ser implementado pelas subclasses.")
