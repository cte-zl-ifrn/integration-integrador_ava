import logging
import requests
import re
import json
import sentry_sdk
from http.client import HTTPException
from integrador.models import Ambiente
from integrador.models import Solicitacao, Campus, Curso


CODIGO_DIARIO_REGEX = re.compile("^(\\d\\d\\d\\d\\d)\\.(\\d*)\\.(\\d*)\\.(.*)\\.(\\w*\\.\\d*)(#\\d*)?$")
CODIGO_DIARIO_ANTIGO_ELEMENTS_COUNT = 5
CODIGO_DIARIO_NOVO_ELEMENTS_COUNT = 6
CODIGO_DIARIO_SEMESTRE_INDEX = 0
CODIGO_DIARIO_PERIODO_INDEX = 1
CODIGO_DIARIO_CURSO_INDEX = 2
CODIGO_DIARIO_TURMA_INDEX = 3
CODIGO_DIARIO_DISCIPLINA_INDEX = 4
CODIGO_DIARIO_ID_DIARIO_INDEX = 5

CODIGO_COORDENACAO_REGEX = re.compile("^(\\w*)\\.(\\d*)(.*)*$")
CODIGO_COORDENACAO_ELEMENTS_COUNT = 3
CODIGO_COORDENACAO_CAMPUS_INDEX = 0
CODIGO_COORDENACAO_CURSO_INDEX = 1
CODIGO_COORDENACAO_SUFIXO_INDEX = 2

CODIGO_PRATICA_REGEX = re.compile("^(\\d\\d\\d\\d\\d)\\.(\\d*)\\.(\\d*)\\.(.*)\\.(\\d{11,14}\\d*)$")
CODIGO_PRATICA_ELEMENTS_COUNT = 5
CODIGO_PRATICA_SUFIXO_INDEX = 4


class SyncError(Exception):
    def __init__(self, message, code, campus=None, retorno=None, params=None):
        super().__init__(message, code, params)
        self.message = message
        self.code = code
        self.campus = campus
        self.retorno = retorno


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
        url = f"{ava.base_api_url}/?{service}&{querystring}"
        content = get_json(url, headers={"Authentication": f"Token {ava.token}"})
        return content
    except Exception as e:
        logging.error(e)
        sentry_sdk.capture_exception(e)


class MoodleBroker:

    def _validate_campus(self, pkg: dict):
        try:
            filter = {
                "suap_id": pkg["campus"]["id"],
                "sigla": pkg["campus"]["sigla"],
                "active": True,
            }
        except Exception:
            raise SyncError("O JSON não tinha a estrutura definida.", 406)

        campus = Campus.objects.filter(**filter).first()
        if campus is None:
            raise SyncError(
                f"""Não existe um campus com o id '{filter['suap_id']}' e a sigla '{filter['sigla']}'.""",
                404,
            )

        if not campus.active:
            raise SyncError(f"O campus '{filter['sigla']}' existe, mas está inativo.", 412)

        if not campus.ambiente.active:
            raise SyncError(
                f"""O campus '{filter['sigla']}' existe e está ativo, mas o ambiente {campus.ambiente.nome} está inativo.""",  # noqa
                417,
            )
        return campus

    def sync(self, recebido: dict):
        retorno = None
        solicitacao = None
        try:
            solicitacao = Solicitacao.objects.create(recebido=recebido, status=Solicitacao.Status.PROCESSANDO)

            solicitacao.campus = self._validate_campus(recebido)
            try:
                coortes = Curso.objects.get(codigo=recebido["curso"]["codigo"]).coortes
            except:
                coortes = []
            solicitacao.enviado = dict(**recebido, **{"coortes": coortes})
            solicitacao.save()

            retorno = requests.post(
                solicitacao.campus.sync_up_enrolments_url,
                json=solicitacao.enviado,
                headers=solicitacao.campus.credentials,
            )

            solicitacao.respondido = json.loads(retorno.text)
            solicitacao.status = Solicitacao.Status.SUCESSO
            solicitacao.status_code = retorno.status_code
            solicitacao.save()

            return solicitacao
        except Exception as e:
            error_message = getattr(retorno, "text", "-")
            error_text = f"""
                Erro na integração. O AVA retornou um erro.
                Contacte um administrador.
                Erro: {e}.
                Cause: {error_message}
            """
            if solicitacao is not None:
                solicitacao.respondido = {"error": {"error_message": f"{e}", "error": f"{error_message}"}}
                solicitacao.status = Solicitacao.Status.FALHA
                solicitacao.status_code = getattr(e, "code", getattr(retorno, "status_code", 500))
                solicitacao.save()
            raise SyncError(error_text, getattr(e, "code", getattr(retorno, "status_code", 500)))
