import logging
import requests
import re
import json
import sentry_sdk
from http.client import HTTPException
from edu.models import Curso, Polo, Programa
from coorte.models import Coorte, dados_vinculo
from integrador.models import Ambiente, Solicitacao


logger = logging.getLogger(__name__)


class SyncError(Exception):
    def __init__(self, message, code, retorno=None, params=None):
        super().__init__(message, code, params)
        self.message = message
        self.code = code
        self.retorno = retorno
        logger.debug(f"{code}: {message} - {retorno}")


def requests_get(url, headers={}, encoding="utf-8", decode=True, **kwargs):
    response = requests.get(url, headers=headers, **kwargs)

    if response.ok:
        byte_array_content = response.content
        return byte_array_content.decode(encoding) if decode and encoding is not None else byte_array_content
    else:
        exc = HTTPException("%s - %s" % (response.status_code, response.reason))
        exc.status = response.status_code
        exc.reason = response.reason
        exc.headers = response.headers
        exc.url = url
        raise exc


def get_json(url, headers={}, encoding="utf-8", json_kwargs=None, **kwargs):
    content = requests_get(url, headers=headers, encoding=encoding, **kwargs)
    return json.loads(content, **(json_kwargs or {}))


def get_json_api(ava: Ambiente, service: str, **params: dict):
    try:
        if params is not None:
            querystring = "&".join([f"{k}={v}" for k, v in params.items() if v is not None])
        else:
            querystring = ""
        url = f"{ava.moodle_base_api_url}/?{service}&{querystring}"
        content = get_json(url, headers={"Authentication": f"Token {ava.token}"})
        return content
    except Exception as e:
        logging.error(e)
        sentry_sdk.capture_exception(e)
        raise e


def post_json_api(ava: Ambiente, service: str, jsonbody: dict):
    try:
        retorno = requests.post(
            url=f"{ava.moodle_base_api_url}/?{service}",
            headers=ava.credentials,
            json=jsonbody,
        )
        
        # Verifica se a resposta foi bem-sucedida
        if not retorno.ok:
            raise SyncError(
                f"Erro ao se comunicar com o Moodle: HTTP {retorno.status_code}. Texto recebido: {retorno.text[:500]}",
                retorno.status_code,
                retorno=retorno.text
            )
        
        try:
            return json.loads(retorno.text)
        except json.JSONDecodeError as json_error:
            raise SyncError(
                f"Erro ao se comunicar com o Moodle: Ocorreu um erro: {json_error}. Texto recebido: {retorno.text[:500]}",
                502,
                retorno=retorno.text
            )
    except SyncError:
        raise
    except Exception as e:
        logging.error(e)
        sentry_sdk.capture_exception(e)
        raise SyncError(
            f"Erro inesperado ao se comunicar com o Moodle: {str(e)}",
            500
        )

