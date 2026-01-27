# Monitoramento de Erros CSRF com Sentry

## Visão Geral

Foi implementado um sistema de monitoramento de erros CSRF que captura e envia automaticamente informações detalhadas para o Sentry sempre que uma requisição falha na verificação CSRF.

## Arquivos Modificados/Criados

### 1. `src/integrador/views_errors.py` (NOVO)
View customizada para tratar falhas de verificação CSRF.

**Funcionalidades:**
- Captura informações detalhadas da requisição que falhou
- Envia notificação para o Sentry com contexto completo
- Detecta automaticamente o tipo de resposta esperado (JSON ou HTML)
- Registra log local para debug

**Detecção de tipo de resposta (em ordem de prioridade):**
1. Se `Content-Type` é `application/json` → retorna JSON
2. Se header `Accept` contém `application/json` → retorna JSON
3. Se path começa com `/api/` → retorna JSON
4. Caso contrário → retorna HTML

**Informações capturadas:**
- Path e método da requisição
- User Agent do cliente
- Endereço IP remoto
- HTTP Referer
- Content Type
- Razão da falha CSRF
- Informações do usuário (se autenticado)

### 2. `src/settings/securities.py` (MODIFICADO)
Configuração atualizada para usar a view customizada:
```python
CSRF_FAILURE_VIEW = env("DJANGO_CSRF_FAILURE_VIEW", "integrador.views_errors.csrf_failure")
```

### 3. `src/integrador/templates/403_csrf.html` (NOVO)
Template HTML personalizado para exibir erro CSRF de forma amigável.
Segue o mesmo padrão visual dos templates 404.html e 500.html do projeto, mantendo consistência no design.

## Como Funciona

### Fluxo de Execução

1. **Requisição chega ao servidor** → Django valida o token CSRF
2. **Validação falha** → Django chama `CSRF_FAILURE_VIEW`
3. **View customizada é executada** → `csrf_failure()` em `views_errors.py`
4. **Captura de informações** → Coleta dados da requisição
5. **Envio para Sentry** → Registra no Sentry com tags e contexto
6. **Log local** → Registra warning no log do Django
7. **Resposta ao cliente** → Retorna JSON (APIs) ou HTML (navegadores)

### Informações no Sentry

Cada erro CSRF enviado ao Sentry inclui:

**Tags:**
- `error_type: "csrf_failure"`
- `csrf_reason: <motivo específico>`

**Contextos:**
- **csrf_failure:** path, method, referer, reason
- **client:** IP, user agent
- **user:** id, username, email (se autenticado)

**Nível:** `warning`

## Testando a Implementação

### 1. Teste via cURL (Requisição sem token CSRF)
```bash
# Deve retornar JSON com status 403
curl -X POST http://localhost:8091/api/algum-endpoint/ \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### 2. Testar usando o container
```bash
ava exec integrador python test_csrf_monitoring.py http://localhost:8091
```

### 3. Verificar no Sentry
1. Acesse seu dashboard do Sentry
2. Filtre por tag: `error_type:csrf_failure`
3. Verifique os detalhes capturados

## Configuração do Sentry

Certifique-se de que o Sentry está configurado corretamente em `settings/observabilities.py`:

```bash
# Variável de ambiente necessária
SENTRY_DNS=https://your-sentry-dsn@sentry.io/project-id
```

Outras variáveis opcionais:
- `SENTRY_ENVIRONMENT`: Define o ambiente (local, dev, prod)
- `SENTRY_SAMPLE_RATE`: Taxa de amostragem de erros (0-100)
- `SENTRY_SEND_DEFAULT_PII`: Envia informações pessoais (default: True)

## Benefícios

1. **Visibilidade Total:** Agora você sabe quando sistemas externos falham ao acessar a API
2. **Debug Facilitado:** Informações completas da requisição facilitam identificar problemas
3. **Monitoramento Proativo:** Alertas no Sentry permitem ação rápida
4. **Análise de Padrões:** Tags permitem identificar origens problemáticas
5. **Resposta Apropriada:** Clientes recebem mensagens claras sobre o erro

## URLs Isentas de CSRF

O middleware `DisableCSRFForAPIMiddleware` já isenta algumas URLs:
- `/api/enviar_diarios/`
- `/api/baixar_notas/`
- `/__debug__/` (Django Debug Toolbar)

Para adicionar novas URLs isentas, edite `src/integrador/middleware.py`:
```python
CSRF_EXEMPT_URLS = [
    re.compile(r'^api/nova-rota/'),
    # ... outros padrões
]
```

## Troubleshooting

### Erro não aparece no Sentry
1. Verifique se `SENTRY_DNS` está configurado
2. Confirme que o Sentry está inicializado (veja logs na inicialização)
3. Verifique `SENTRY_SAMPLE_RATE` (deve ser > 0)

### Template 403_csrf.html não é exibido
1. Verifique se o template está em `integrador/templates/`
2. Confirme que `integrador` está em `INSTALLED_APPS`
3. O fallback HTML será usado se o template não existir

### Ainda recebo erro padrão do Django
1. Confirme que `CSRF_FAILURE_VIEW` está configurado corretamente
2. Reinicie o servidor Django após alterações
3. Verifique logs de erro do Django

## Logs

Os erros CSRF também são registrados localmente:
```python
logger.warning(
    f"CSRF verification failed: {reason}",
    extra={"request": request, "client_info": client_info}
)
```

Configure o nível de log em `settings/loggings.py` se necessário.

## Próximos Passos

Para melhorias futuras, considere:

1. **Dashboard de Análise:** Criar um dashboard no Sentry para visualizar padrões de falhas CSRF
2. **Alertas Automáticos:** Configurar alertas para picos de erros CSRF
3. **Whitelist Dinâmica:** Sistema para adicionar origens confiáveis via admin
4. **Rate Limiting:** Implementar rate limiting para IPs com muitas falhas CSRF
5. **Documentação da API:** Documentar requisitos de CSRF para integradores

## Referências

- [Django CSRF Protection](https://docs.djangoproject.com/en/stable/ref/csrf/)
- [Sentry Django Integration](https://docs.sentry.io/platforms/python/guides/django/)
- [CSRF Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
