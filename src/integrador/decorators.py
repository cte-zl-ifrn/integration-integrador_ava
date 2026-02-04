import json
import sentry_sdk
import jsonschema
from functools import wraps
from django.http import HttpRequest, JsonResponse
from django.conf import settings
from integrador.models import Ambiente, Solicitacao
from integrador.utils import SyncError


def json_response(func):
    def inner(request: HttpRequest, *args, **kwargs):
        result = func(request, *args, **kwargs)
        return result if isinstance(result, JsonResponse) else JsonResponse(result, safe=False)
    return inner


def detect_ambiente(func):
    def inner(request: HttpRequest, *args, **kwargs):
        request.json_recebido = getattr(request, "json_recebido", {"campus": {"sigla": request.GET.get("campus_sigla")}})
        request.ambiente = Ambiente.objects.seleciona_ambiente(request.json_recebido)

        if getattr(request, "ambiente") is None:
            raise SyncError(f"Não encontramos um Ambiente ativo para o campus {request.GET.get('campus_sigla')}", 404)

        return JsonResponse(func(request, *args, **kwargs), safe=False)
    return inner


def exception_as_json(func):
    def inner(request: HttpRequest, *args, **kwargs):
        def __response_error(request: HttpRequest, error: Exception):
            event_id = sentry_sdk.capture_exception(error)
            error_json = {
                "code": getattr(error, "code", 500),
                "error": getattr(error, "message", f"{error}"),
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
            raise SyncError("Method HTTP não autorizado.", 501)
        return func(request, *args, **kwargs)

    return inner


def check_is_get(func):
    def inner(request: HttpRequest, *args, **kwargs):
        if request.method != "GET":
            raise SyncError("Não implementado.", 501)
        return func(request, *args, **kwargs)

    return inner


def check_json(operacao: str):
    def decorator(func):
        @wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            try:
                message = request.body.decode("utf-8")
                try:
                    request.json_recebido = json.loads(message)

                    # # TODO: Remover comentário após corrigir todos os schemas
                    # try:
                    #     jsonschema.validate(instance=request.json_recebido, schema=operacao.schema)
                    # except Exception as e3:
                    #     parts = e3.message.split("Failed")
                    #     if len(parts) > 1:
                    #         request.json_recebido = {
                    #             "error": {"code": 411, "message": parts[0]},
                    #             "request_message": request.json_recebido
                    #         }
                    #     else:
                    #         request.json_recebido = {
                    #             "error": {"code": 410, "message": e3.message},
                    #             "request_message": request.json_recebido
                    #         }
                except Exception as e2:
                    request.json_recebido = {
                        "error": {"code": 512, "message": f"Foi enviado um JSON mal formado ou nem é JSON ({e2})."},
                        "request_message": message
                    }
            except Exception as e1:
                request.json_recebido = {
                    "error": {"code": 405, "message": f"Erro ao decodificar o body em utf-8 ({e1})."},
                    "request_message": message
                }
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def try_solicitacao(operacao: str):
    def decorator(func):
        @wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            solicitacao = None
            request.json_recebido = getattr(request, "json_recebido", {"error": {"code": 400, "message": f"Não consegui ler o JSON."}})

            if "error" in request.json_recebido:
                raise SyncError(
                    request.json_recebido["error"].get("message", "Erro desconhecido."),
                    request.json_recebido["error"].get("code", 400),
                )

            try:
                campus_sigla = request.json_recebido.get("campus", {}).get("sigla", "-")
                codigo_turma = request.json_recebido.get("turma", {}).get("codigo", "-")
                sigla_componente = request.json_recebido.get("componente", {}).get("sigla", ".")
                if request.GET.get('diario_id') is not None:
                    request.json_recebido["diario"] = {"id": int(request.GET["diario_id"])}
                id_diario = str(request.json_recebido.get("diario", {}).get("id", "#-"))
                diario_codigo=f"{campus_sigla}:{codigo_turma}.{sigla_componente}#{id_diario}"

                solicitacao = Solicitacao.objects.create(
                    ambiente=request.ambiente,
                    campus_sigla=campus_sigla,
                    diario_id=id_diario,
                    diario_codigo=diario_codigo,
                    recebido=request.json_recebido, 
                    status=Solicitacao.Status.PROCESSANDO,
                    operacao=operacao,
                    tipo=request.json_recebido.get("tipo_diario", 'diario'),
                )
                
                if request.ambiente is None:
                    raise SyncError("Ambiente não encontrado ou não ativo.", 404)
                
                request.solicitacao = solicitacao
                
                # Tudo validado
                solicitacao.respondido = func(request, *args, **kwargs)
            
                solicitacao.status = Solicitacao.Status.SUCESSO
                solicitacao.status_code = 200
                solicitacao.save()

                return solicitacao.respondido
            except Exception as e:
                error_text = f"""
                    Erro na integração. O AVA retornou um erro. Contacte um administrador. Erro:\n{e}.
                """
                if solicitacao is not None:
                    solicitacao.respondido = {"error": {"error_message": f"{e}", "error": f"{e}"}}
                    solicitacao.status = Solicitacao.Status.FALHA
                    solicitacao.status_code = getattr(e, "code", 500)
                    solicitacao.save()
                    raise SyncError(error_text, solicitacao.status_code)
                raise SyncError(error_text, 500)
        return wrapper
    return decorator
