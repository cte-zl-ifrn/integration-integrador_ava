⚙️ Testes para App Settings

Cobertura:

1. SettingsAppsTestCase - Configuração de apps
   - ✅ APP_LABEL, APP_VERSION, APP_LAST_STARTUP
   - ✅ INSTALLED_APPS (Django, custom, terceiros)
   - ✅ SHOW_SUPPORT_FORM, SHOW_SUPPORT_CHAT
2. SettingsDatabasesTestCase - Banco de dados
   - ✅ Configuração default
   - ✅ Engine PostgreSQL
   - ✅ Porta válida
   - ✅ DEFAULT_AUTO_FIELD
3. SettingsSecuritiesTestCase - Segurança
   - ✅ SECRET_KEY
   - ✅ URLs de login/logout
   - ✅ CORS
   - ✅ CSRF
   - ✅ OAuth
   - ✅ SUAP
4. SettingsDevelopmentsTestCase - Desenvolvimento
   - ✅ DEBUG booleano
   - ✅ Debug toolbar
   - ✅ Middleware de debug
5. SettingsCachesTestCase - Cache
   - ✅ Configuração default
   - ✅ Backend Redis
   - ✅ Location
6. SettingsEnvironmentVariablesTestCase - Variáveis de ambiente
   - ✅ DJANGO_DEBUG
   - ✅ POSTGRES_*
   - ✅ SECRET_KEY
7. SettingsIntegrationTestCase - Integração
   - ✅ Configurações obrigatórias
   - ✅ Ordem das apps
   - ✅ Ordem dos middlewares
   - ✅ Conexão com banco
   - ✅ Cache funcional
8. SettingsSecurityTestCase - Segurança
   - ✅ SECRET_KEY não é default
   - ✅ DEBUG em produção
   - ✅ ALLOWED_HOSTS
   - ✅ SSL redirect
   - ✅ Cookies secure
9. SettingsEdgeCasesTestCase - Casos extremos
   - ✅ INSTALLED_APPS não vazio
   - ✅ MIDDLEWARE não vazio
   - ✅ Nomes de banco/usuário
   - ✅ Sem variáveis de ambiente
10. SettingsPerformanceTestCase - Performance
    - ✅ Import rápido
    - ✅ Pool de conexões
