import logging
from integrador.utils import SyncError, http_get_json, http_post_json
from integrador.brokers.base import BaseBroker

logger = logging.getLogger(__name__)

_SYNC_UP_REQUIRED_FIELDS = {
    "campus": ["id", "sigla", "descricao"],
    "curso": ["id", "codigo", "nome"],
    "turma": ["id", "codigo"],
    "componente": ["id", "sigla", "descricao"],
    "diario": ["id", "sigla", "situacao"],
}


class Suap2LocalSuapBroker(BaseBroker):
    @property
    def moodle_base_api_url(self):
        return f"{self.solicitacao.ambiente.base_url}/local/suap/api"

    def __get_service_url(self, service: str) -> str:
        logger.debug(f"{self.moodle_base_api_url}/index.php?{service}")
        return f"{self.moodle_base_api_url}/index.php?{service}"

    def __get_json(self, service: str, **params: dict):
        querystring = "&".join([f"{k}={v}" for k, v in params.items() if v is not None]) if params is not None else ""
        result = http_get_json(f"{self.__get_service_url(service)}&{querystring}", headers=self.credentials)
        logger.debug(f"Response: {result}")
        return result

    def __post_json(self, service: str, jsonbody: dict):
        result = http_post_json(self.__get_service_url(service), jsonbody, self.credentials)
        return result

    def _validate_sync_payload(self, payload: dict) -> None:
        missing = [
            f"{field}.{sub}" if field in payload else field
            for field, subfields in _SYNC_UP_REQUIRED_FIELDS.items()
            for sub in (subfields if field in payload else [""])
            if field not in payload or sub not in payload[field]
        ]
        if missing:
            raise SyncError(
                f"Campos obrigatórios ausentes no payload de sync_up_enrolments: {', '.join(missing)}.",
                422,
            )

    def sync_up_enrolments(self) -> dict:
        self._validate_sync_payload(self.solicitacao.recebido)
        try:
            self.solicitacao.enviado = dict(**self.solicitacao.recebido, **{"coortes": self.get_cohort()})
            self.solicitacao.save()
        except SyncError:
            raise
        except Exception as e:
            raise SyncError(
                f"Erro ao tentar obter as coortes antes de iniciar a integração com o AVA. Contacte um administrador. Erro: {e}.",
                getattr(e, "code", 525),
            )

        result = self.__post_json("sync_up_enrolments", self.solicitacao.enviado)
        result["ambiente"] = self.solicitacao.ambiente.base_url
        return result

    def sync_down_grades(self) -> dict:
        return self.__get_json("sync_down_grades", diario_id=self.solicitacao.diario_id)
