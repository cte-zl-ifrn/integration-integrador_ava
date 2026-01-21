import logging
from integrador.utils import SyncError, http_get_json, http_post_json
from integrador.brokers.base import BaseBroker


logger = logging.getLogger(__name__)


class Suap2LocalSuapBroker(BaseBroker):

    @property
    def moodle_base_api_url(self):
        return f"{self.solicitacao.ambiente.base_url}/local/suap/api"


    def __get_service_url(self, service: str) -> str:
        print(f"{self.moodle_base_api_url}/index.php?{service}")
        return f"{self.moodle_base_api_url}/index.php?{service}"
   

    def __get_json(self, service: str, **params: dict):
        querystring = "&".join([f"{k}={v}" for k, v in params.items() if v is not None]) if params is not None else ""
        print(http_get_json(f"{self.__get_service_url(service)}&{querystring}", headers=self.credentials))
        return []


    def __post_json(self, service: str, jsonbody: dict):
        return http_post_json(self.__get_service_url(service), jsonbody, self.credentials)


    def sync_up_enrolments(self) -> dict:
        try:
            self.solicitacao.enviado = dict(**self.solicitacao.recebido, **{"coortes": self.get_coortes()})
            self.solicitacao.save()
        except Exception as e:
            SyncError(f"Erro ao tentar obter as coortes antes de iniciar a integração com o AVA. Contacte um administrador. Erro: {e}.", getattr(e, "code", 525))

        return self.__post_json('sync_up_enrolments', self.solicitacao.enviado)


    def sync_down_grades(self) -> dict:
        return self.__get_json("sync_down_grades", diario_id=self.solicitacao.diario_id)