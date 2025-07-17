import logging
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.http import HttpRequest, JsonResponse
from integrador.models import Ambiente, Solicitacao
from integrador.brokers import get_json_api, SyncError, MoodleBroker
from integrador.decorators import (
    json_response,
    exception_as_json,
    check_is_post,
    check_is_get,
    valid_token,
    check_json,
    try_solicitacao,
    detect_ambiente
)


logger = logging.getLogger(__name__)


@csrf_exempt
@transaction.atomic
@json_response
@exception_as_json
@check_is_post
@valid_token
@check_json(Solicitacao.Operacao.SYNC_UP_DIARIO)
@detect_ambiente
@try_solicitacao(Solicitacao.Operacao.SYNC_UP_DIARIO)
def sync_up_enrolments(request: HttpRequest = None) -> dict:
    return MoodleBroker().sync_up_enrolments(request.solicitacao)


@csrf_exempt
@transaction.atomic
@json_response
@exception_as_json
@check_is_get
@valid_token
@detect_ambiente
@try_solicitacao(Solicitacao.Operacao.SYNC_DOWN_NOTAS)
def sync_down_grades(request: HttpRequest):

    if getattr(request, "ambiente") is None:
        raise SyncError(f"Não encontramos um Ambiente ativo para o campus {request.GET.get('campus_sigla')}", 404)
    
    request.solicitacao.diario_id = int(request.GET.get('diario_id', 0))
    request.solicitacao.save()
    
    return get_json_api(request.ambiente, "sync_down_grades", diario_id=request.solicitacao.diario_id)
