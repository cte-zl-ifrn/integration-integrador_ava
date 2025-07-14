import logging
import requests
import re
import json
import sentry_sdk
from http.client import HTTPException
from edu.models import Curso, Polo, Programa
from coorte.models import Coorte, dados_vinculo
from integrador.models import Ambiente, Solicitacao

import logging

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


class MoodleBroker:

    def sync(self, recebido: dict):
        retorno = None
        solicitacao = None
        try:
            ambiente = Ambiente.objects.seleciona_ambiente(recebido)

            if ambiente is None:
                raise SyncError(
                    "Ambiente não encontrado ou não ativo.",
                    404,
                    retorno=None,
                    params={"recebido": recebido}
                )


            print(ambiente.sync_up_enrolments_url)

            solicitacao = Solicitacao.objects.create(
                ambiente=ambiente,
                campus_sigla=recebido.get("campus", {}).get("sigla", "-"),
                diario_codigo=(
                    recebido.get("turma", {}).get("codigo", "-") + '.' +
                    recebido.get("componente", {}).get("sigla", ".") + '#' +
                    str(recebido.get("diario", {}).get("id", "#-"))
                ),
                diario_id=recebido.get("diario", {}).get("id"),
                recebido=recebido, 
                status=Solicitacao.Status.PROCESSANDO
            )

            coortes = []
            try:
                curso, created = Curso.objects.get_or_create(
                    suap_id=recebido["curso"]["id"],
                    codigo=recebido["curso"]["codigo"],
                    nome=recebido["curso"]["nome"],
                    descricao=recebido["curso"]["descricao"],
                )
                if created:
                    print(f"O curso foi criado {curso.nome}")
                else:
                    coortes += Coorte.objects.filter(coortecurso__curso=curso)
            except:
                pass

            try:
                programas_set = set([a.get("programa") for a in recebido.get("alunos", [])])
                for p in programas_set:
                    programa, created = Programa.objects.get_or_create(sigla=p, nome=p)
                    if created:
                        print(f"O programa foi criado {programa.sigla}")
                    else:
                        coortes += Coorte.objects.filter(coorteprograma__programa=programa)
            except:
                pass

            try:
                polos_set = set([a.get("polo", {}).get("descricao") for a in recebido.get("alunos", [])])
                for p in Polo.objects.filter(nome__in=polos_set):
                    coortes += Coorte.objects.filter(coortepolo__polo=p)
            except:
                pass

            objects_list = [
                {
                    "idnumber": coo.papel.sigla,
                    "nome": coo.papel.nome,
                    "ativo": coo.papel.active,
                    "role": coo.papel.papel,
                    "descricao": coo.papel.nome,
                    "colaboradores": (
                        [dados_vinculo(vinc) for vinc in coo.vinculos.all()] if hasattr(coo, "vinculos") else None
                    ),
                }
                for coo in coortes
            ]

            object_unique = list(objects_list)

            solicitacao.enviado = dict(**recebido, **{"coortes": object_unique})
            solicitacao.save()

            retorno = requests.post(ambiente.sync_up_enrolments_url, json=solicitacao.enviado, headers=ambiente.credentials)

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
