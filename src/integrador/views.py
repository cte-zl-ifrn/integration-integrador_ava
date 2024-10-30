import json
import sentry_sdk
import jsonschema
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.conf import settings
from integrador.models import Campus
from django.shortcuts import get_object_or_404
from integrador.brokers import get_json_api, SyncError, MoodleBroker


def exception_as_json(func):
    def inner(request: HttpRequest, *args, **kwargs):
        def __response_error(request: HttpRequest, error: Exception):
            event_id = sentry_sdk.capture_exception(error)
            error_json = {
                "error": getattr(error, "message", None),
                "code": getattr(error, "code", 500),
                "event_id": event_id,
            }

            return JsonResponse(error_json, status=getattr(error, "code", 500))

        try:
            return func(request, *args, **kwargs)
        except SyncError as se:
            return __response_error(request, se)
        except Exception as e2:
            return __response_error(request, e2)

    return inner


def valid_token(func):
    def inner(request: HttpRequest, *args, **kwargs):
        if not hasattr(settings, "SUAP_INTEGRADOR_KEY"):
            raise SyncError("Você se esqueceu de configurar a settings 'SUAP_INTEGRADOR_KEY'.", 428)

        if "HTTP_AUTHENTICATION" not in request.META:
            raise SyncError("Envie o token de autenticação no header.", 431)

        if f"Token {settings.SUAP_INTEGRADOR_KEY}" != request.META["HTTP_AUTHENTICATION"]:
            raise SyncError(
                "Você enviou um token de autenticação diferente do que tem na settings 'SUAP_INTEGRADOR_KEY'.",
                403,  # noqa
            )
        return func(request, *args, **kwargs)

    return inner


def check_is_post(func):
    def inner(request: HttpRequest, *args, **kwargs):
        if request.method != "POST":
            raise SyncError("Não implementado.", 501)
        return func(request, *args, **kwargs)

    return inner


def check_is_get(func):
    def inner(request: HttpRequest, *args, **kwargs):
        if request.method != "GET":
            raise SyncError("Não implementado.", 501)
        return func(request, *args, **kwargs)

    return inner


@csrf_exempt
@transaction.atomic
@exception_as_json
@check_is_post
@valid_token
def sync_up_enrolments(request: HttpRequest):
    try:
        message_string = request.body.decode("utf-8")
    except Exception as e1:
        return SyncError(f"Erro ao decodificar o body em utf-8 ({e1}).", 405)

    try:
        with open("integrador/static/diario.schema.json") as f:
            message = json.dumps(message_string)
            schema = json.load(f.read())
            jsonschema.validate(instance=message, schema=schema)
        return JsonResponse(MoodleBroker().sync(message).respondido, safe=False)
    except Exception as e1:
        return SyncError(f"Erro ao converter para JSON ({e1}).", 407)


@csrf_exempt
@exception_as_json
@check_is_get
@valid_token
def sync_down_grades(request: HttpRequest):
    campus = get_object_or_404(Campus, sigla=request.GET.get("campus_sigla"))
    diario_id = int(request.GET.get("diario_id"))
    notas = get_json_api(campus.ambiente, "sync_down_grades", diario_id=diario_id)
    return JsonResponse(notas, safe=False)
