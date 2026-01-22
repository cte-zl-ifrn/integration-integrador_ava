# Models:

- AmbienteModelTestCase: Modelo Ambiente com expressão seletora (Rule), manager customizado, validação de regras, propriedade base_url
- SolicitacaoModelTestCase: Modelo Solicitacao com JSON fields, auto-população de campos, choices de Status/Operacao, status_merged


# Utils:

- SyncErrorTestCase: Classe de erro customizada
- UtilsFunctionsTestCase: http_get, http_post, http_get_json, http_post_json, validate_http_response


# Decorators (8 decorators testados):

- DecoratorsTestCase: json_response, exception_as_json, valid_token, check_is_post, check_is_get, check_json, detect_ambiente
- TrySolicitacaoDecoratorTestCase: try_solicitacao com sucesso/erro

# Middleware:

- MiddlewareTestCase: DisableCSRFForAPIMiddleware com padrões de URL para isenção de CSRF


# Brokers:

- BaseBrokerTestCase: Classe base com credentials, get_coortes, métodos abstratos
- Suap2LocalSuapBrokerTestCase: Implementação específica com moodle_base_api_url, sync_up_enrolments, sync_down_grades


# Management Commands:

- ManagementCommandTestCase: atualiza_solicitacoes para atualizar registros antigos


# Integration & Edge Cases:

- IntegrationTestCase: Fluxo completo de sync_up_enrolments com todos os decorators
- EdgeCasesTestCase: Múltiplas regras correspondentes, JSON incompleto, expressões complexas, URLs com barra final

Os testes cobrem todos os aspectos críticos da integração entre SUAP e Moodle, incluindo autenticação via token, validação de JSON, seleção de ambiente baseada em regras, tratamento de erros, e comunicação HTTP com o AVA.
