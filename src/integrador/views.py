import logging
from django.db import transaction
from django.http import HttpRequest
from integrador.models import Solicitacao
from integrador.brokers.suap2local_suap import Suap2LocalSuapBroker
from integrador.brokers.suap2tool_sga import Suap2ToolSgaBroker
from integrador.decorators import (
    json_response,
    exception_as_json,
    check_is_post,
    check_is_get,
    valid_token,
    check_json,
    try_solicitacao,
    detect_ambiente,
)

logger = logging.getLogger(__name__)


@transaction.atomic
@json_response
@exception_as_json
@check_is_post
@valid_token
@check_json(Solicitacao.Operacao.SYNC_UP_DIARIO)
@detect_ambiente
@try_solicitacao(Solicitacao.Operacao.SYNC_UP_DIARIO)
def sync_up_enrolments(request: HttpRequest = None) -> dict:
    ambiente = request.solicitacao.ambiente
    if ambiente.can_send_to_local_suap:
        return Suap2LocalSuapBroker(request.solicitacao).sync_up_enrolments()
    elif ambiente.can_send_to_tool_sga:
        return Suap2ToolSgaBroker(request.solicitacao).sync_up_enrolments()
    else:
        raise Exception(
            f"O ambiente {ambiente.ambiente} não está configurado "
            f"para enviar dados para o Local SUAP ou Tool SGA. Contacte um administrador."
        )


@transaction.atomic
@json_response
@exception_as_json
@check_is_get
@valid_token
@detect_ambiente
@try_solicitacao(Solicitacao.Operacao.SYNC_DOWN_NOTAS)
def sync_down_grades(request: HttpRequest):
    return Suap2LocalSuapBroker(request.solicitacao).sync_down_grades()
