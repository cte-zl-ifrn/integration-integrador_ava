# -*- coding: utf-8 -*-
"""
Views customizadas para tratamento de erros.
"""
import logging
import sentry_sdk
from django.views.decorators.csrf import requires_csrf_token
from django.http import JsonResponse, HttpResponse
from django.template import loader

logger = logging.getLogger(__name__)


@requires_csrf_token
def csrf_failure(request, reason=""):
    """
    View customizada para tratar falhas de CSRF.
    
    Esta view é chamada quando uma requisição falha na verificação CSRF.
    Ela captura o erro e envia para o Sentry para monitoramento, além de
    retornar uma resposta adequada ao cliente.
    
    Args:
        request: O objeto HttpRequest que falhou na verificação CSRF
        reason: A razão da falha (fornecida pelo Django)
    
    Returns:
        JsonResponse ou HttpResponse com status 403
    """
    # Captura informações importantes da requisição
    client_info = {
        "path": request.path,
        "method": request.method,
        "user_agent": request.META.get("HTTP_USER_AGENT", "Unknown"),
        "remote_addr": request.META.get("REMOTE_ADDR", "Unknown"),
        "http_referer": request.META.get("HTTP_REFERER", "Unknown"),
        "content_type": request.META.get("CONTENT_TYPE", "Unknown"),
        "reason": reason,
    }
    
    # Log local para debug
    logger.warning(
        f"CSRF verification failed: {reason}",
        extra={
            "request": request,
            "client_info": client_info,
        }
    )
    
    # Envia o erro para o Sentry com contexto adicional
    with sentry_sdk.push_scope() as scope:
        # Adiciona tags para facilitar a filtragem no Sentry
        scope.set_tag("error_type", "csrf_failure")
        scope.set_tag("csrf_reason", reason)
        
        # Adiciona contexto adicional
        scope.set_context("csrf_failure", {
            "reason": reason,
            "path": request.path,
            "method": request.method,
            "referer": request.META.get("HTTP_REFERER", "Unknown"),
        })
        
        scope.set_context("client", {
            "ip": request.META.get("REMOTE_ADDR", "Unknown"),
            "user_agent": request.META.get("HTTP_USER_AGENT", "Unknown"),
        })
        
        # Se o usuário estiver autenticado, adiciona suas informações
        if request.user.is_authenticated:
            scope.set_user({
                "id": request.user.id,
                "username": request.user.username,
                "email": getattr(request.user, "email", ""),
            })
        
        # Captura a mensagem no Sentry
        sentry_sdk.capture_message(
            f"CSRF verification failed: {reason}",
            level="warning"
        )
    
    # Retorna resposta apropriada baseada no tipo de requisição
    # Prioridade: 1) Content-Type é JSON, 2) Accept é JSON, 3) Path é /api/
    content_type = request.META.get("CONTENT_TYPE", "").lower()
    accept_header = request.META.get("HTTP_ACCEPT", "").lower()
    is_json_request = (
        "application/json" in content_type or
        "application/json" in accept_header or
        request.path.startswith("/api/")
    )
    
    if is_json_request:
        # Para requisições de API/JSON, retorna JSON
        return JsonResponse(
            {
                "error": "CSRF verification failed",
                "reason": reason,
                "message": "A verificação CSRF falhou. Certifique-se de incluir um token CSRF válido.",
            },
            status=403
        )
    
    # Para requisições normais, retorna HTML
    try:
        template = loader.get_template("403_csrf.html")
        return HttpResponse(
            template.render({"reason": reason}, request),
            status=403
        )
    except Exception:
        # Fallback se o template não existir
        return HttpResponse(
            f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>403 Forbidden - CSRF Verification Failed</title>
            </head>
            <body>
                <h1>403 Forbidden</h1>
                <p>CSRF verification failed. Request aborted.</p>
                <p>Reason: {reason}</p>
            </body>
            </html>
            """,
            status=403
        )
