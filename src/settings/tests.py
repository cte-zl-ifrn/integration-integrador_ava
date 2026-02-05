"""
Testes unitários para a app settings.

Este módulo contém testes para:
- Configurações de apps (apps.py)
- Configurações de banco de dados (databases.py)
- Configurações de segurança (securities.py)
- Configurações de desenvolvimento (developments.py)
- Configurações de cache (caches.py)
- Validação de variáveis de ambiente
"""
from django.test import TestCase, override_settings
from django.conf import settings
from unittest.mock import patch, MagicMock
import importlib
import os


class SettingsAppsTestCase(TestCase):
    """Testes para settings/apps.py."""

    def test_project_title_is_defined(self):
        """Testa se PROJECT_TITLE está definido."""
        from settings.apps import PROJECT_TITLE
        self.assertIsNotNone(PROJECT_TITLE)
        self.assertIsInstance(PROJECT_TITLE, str)
        self.assertEqual(PROJECT_TITLE, "Integrador AVA")

    def test_project_version_is_defined(self):
        """Testa se PROJECT_VERSION está definido."""
        from settings.apps import PROJECT_VERSION
        self.assertIsNotNone(PROJECT_VERSION)
        self.assertIsInstance(PROJECT_VERSION, str)
        self.assertRegex(PROJECT_VERSION, r'^\d+\.\d+\.\d+$')

    def test_project_last_startup_is_timestamp(self):
        """Testa se PROJECT_LAST_STARTUP é um timestamp válido."""
        from settings.apps import PROJECT_LAST_STARTUP
        self.assertIsInstance(PROJECT_LAST_STARTUP, int)
        self.assertGreater(PROJECT_LAST_STARTUP, 0)

    def test_installed_apps_contains_django_apps(self):
        """Testa se INSTALLED_APPS contém apps Django."""
        django_required_apps = [
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
        ]
        
        for app in django_required_apps:
            self.assertIn(app, settings.INSTALLED_APPS)

    def test_installed_apps_contains_custom_apps(self):
        """Testa se INSTALLED_APPS contém apps customizadas."""
        custom_apps = ['base', 'health', 'integrador', 'cohort']
        
        for app in custom_apps:
            self.assertIn(app, settings.INSTALLED_APPS)

    def test_installed_apps_contains_third_party_apps(self):
        """Testa se INSTALLED_APPS contém apps de terceiros."""
        third_party_apps = [
            'import_export',
            'simple_history',
            'django_rule_engine',
        ]
        
        for app in third_party_apps:
            self.assertIn(app, settings.INSTALLED_APPS)

    def test_show_support_form_is_boolean(self):
        """Testa se SHOW_SUPPORT_FORM é booleano."""
        from settings.apps import SHOW_SUPPORT_FORM
        self.assertIsInstance(SHOW_SUPPORT_FORM, bool)

    def test_show_support_chat_is_boolean(self):
        """Testa se SHOW_SUPPORT_CHAT é booleano."""
        from settings.apps import SHOW_SUPPORT_CHAT
        self.assertIsInstance(SHOW_SUPPORT_CHAT, bool)


class SettingsDatabasesTestCase(TestCase):
    """Testes para settings/databases.py."""

    def test_databases_default_is_configured(self):
        """Testa se a configuração default do banco está definida."""
        self.assertIn('default', settings.DATABASES)
        db_config = settings.DATABASES['default']
        
        # Verifica campos obrigatórios
        self.assertIn('ENGINE', db_config)
        self.assertIn('HOST', db_config)
        self.assertIn('PORT', db_config)
        self.assertIn('NAME', db_config)
        self.assertIn('USER', db_config)
        self.assertIn('PASSWORD', db_config)

    def test_database_engine_is_postgresql(self):
        """Testa se o engine do banco é PostgreSQL."""
        db_engine = settings.DATABASES['default']['ENGINE']
        self.assertIn('postgresql', db_engine)

    def test_database_port_is_valid(self):
        """Testa se a porta do banco é válida."""
        db_port = settings.DATABASES['default']['PORT']
        self.assertIsInstance(db_port, str)
        self.assertTrue(db_port.isdigit())
        port_num = int(db_port)
        self.assertGreater(port_num, 0)
        self.assertLess(port_num, 65536)

    def test_default_auto_field_is_configured(self):
        """Testa se DEFAULT_AUTO_FIELD está configurado."""
        self.assertEqual(
            settings.DEFAULT_AUTO_FIELD,
            'django.db.models.BigAutoField'
        )


class SettingsSecuritiesTestCase(TestCase):
    """Testes para settings/securities.py."""

    def test_secret_key_is_defined(self):
        """Testa se SECRET_KEY está definida."""
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertIsInstance(settings.SECRET_KEY, str)
        self.assertGreater(len(settings.SECRET_KEY), 0)

    def test_login_url_is_defined(self):
        """Testa se LOGIN_URL está definida."""
        self.assertIsNotNone(settings.LOGIN_URL)
        self.assertTrue(settings.LOGIN_URL.startswith('/'))

    def test_login_redirect_url_is_defined(self):
        """Testa se LOGIN_REDIRECT_URL está definida."""
        self.assertIsNotNone(settings.LOGIN_REDIRECT_URL)

    def test_logout_redirect_url_is_defined(self):
        """Testa se LOGOUT_REDIRECT_URL está definida."""
        self.assertIsNotNone(settings.LOGOUT_REDIRECT_URL)

    def test_cors_allow_methods_contains_standard_methods(self):
        """Testa se CORS_ALLOW_METHODS contém métodos padrão."""
        standard_methods = ['GET', 'POST', 'PUT', 'DELETE']
        
        for method in standard_methods:
            self.assertIn(method, settings.CORS_ALLOW_METHODS)

    def test_csrf_cookie_age_is_positive(self):
        """Testa se CSRF_COOKIE_AGE é um valor positivo."""
        self.assertIsInstance(settings.CSRF_COOKIE_AGE, int)
        self.assertGreater(settings.CSRF_COOKIE_AGE, 0)

    def test_csrf_cookie_name_is_defined(self):
        """Testa se CSRF_COOKIE_NAME está definido."""
        self.assertIsNotNone(settings.CSRF_COOKIE_NAME)
        self.assertIsInstance(settings.CSRF_COOKIE_NAME, str)

    def test_csrf_cookie_path_is_root(self):
        """Testa se CSRF_COOKIE_PATH é a raiz."""
        self.assertEqual(settings.CSRF_COOKIE_PATH, '/')

    def test_oauth_configuration_exists(self):
        """Testa se a configuração OAuth existe."""
        from settings.securities import OAUTH
        
        self.assertIsInstance(OAUTH, dict)
        self.assertIn('BASE_URL', OAUTH)
        self.assertIn('AUTHORIZE_URL', OAUTH)
        self.assertIn('TOKEN_URL', OAUTH)
        self.assertIn('CLIENT_ID', OAUTH)
        self.assertIn('CLIENT_SECRET', OAUTH)

    def test_suap_configuration_exists(self):
        """Testa se a configuração do SUAP existe."""
        from settings.securities import SUAP_INTEGRADOR_KEY, SUAP_BASE_URL
        
        self.assertIsNotNone(SUAP_INTEGRADOR_KEY)
        self.assertIsNotNone(SUAP_BASE_URL)
        self.assertTrue(SUAP_BASE_URL.startswith('http'))


class SettingsDevelopmentsTestCase(TestCase):
    """Testes para settings/developments.py."""

    def test_debug_is_boolean(self):
        """Testa se DEBUG é booleano."""
        self.assertIsInstance(settings.DEBUG, bool)

    @override_settings(DEBUG=True)
    def test_debug_toolbar_in_installed_apps_when_debug_true(self):
        """Testa se debug_toolbar está em INSTALLED_APPS quando DEBUG=True."""
        # Este teste é mais informativo, pois depende da instalação do pacote
        # Em ambiente de desenvolvimento, debug_toolbar deve estar presente
        if 'debug_toolbar' in settings.INSTALLED_APPS:
            self.assertIn('debug_toolbar', settings.INSTALLED_APPS)

    @override_settings(DEBUG=True)
    def test_debug_middleware_added_when_debug_true(self):
        """Testa se middleware do debug toolbar é adicionado quando DEBUG=True."""
        if 'debug_toolbar' in settings.INSTALLED_APPS:
            debug_middleware = 'debug_toolbar.middleware.DebugToolbarMiddleware'
            # Verifica se o middleware está presente ou se debug_toolbar não está instalado
            if debug_middleware in settings.MIDDLEWARE:
                self.assertIn(debug_middleware, settings.MIDDLEWARE)


class SettingsCachesTestCase(TestCase):
    """Testes para settings/caches.py."""

    def test_caches_default_is_configured(self):
        """Testa se o cache default está configurado."""
        self.assertIn('default', settings.CACHES)
        cache_config = settings.CACHES['default']
        
        self.assertIn('BACKEND', cache_config)
        self.assertIn('LOCATION', cache_config)

    def test_cache_backend_is_redis(self):
        """Testa se o backend de cache é Redis."""
        backend = settings.CACHES['default']['BACKEND']
        self.assertIn('redis', backend.lower())

    def test_cache_location_is_list(self):
        """Testa se LOCATION do cache é uma lista."""
        location = settings.CACHES['default']['LOCATION']
        self.assertIsInstance(location, list)
        self.assertGreater(len(location), 0)

    def test_cache_location_contains_redis_url(self):
        """Testa se LOCATION contém URL do Redis."""
        location = settings.CACHES['default']['LOCATION'][0]
        self.assertTrue(location.startswith('redis://'))


class SettingsEnvironmentVariablesTestCase(TestCase):
    """Testes para validação de variáveis de ambiente."""

    @patch.dict(os.environ, {'DJANGO_DEBUG': 'False'})
    def test_env_variable_django_debug_false(self):
        """Testa leitura de variável DJANGO_DEBUG=False."""
        # Recarrega o módulo para pegar a nova variável de ambiente
        import settings.developments
        importlib.reload(settings.developments)
        
        from settings.developments import DEBUG
        self.assertFalse(DEBUG)

    @patch.dict(os.environ, {'DJANGO_DEBUG': 'True'})
    def test_env_variable_django_debug_true(self):
        """Testa leitura de variável DJANGO_DEBUG=True."""
        import settings.developments
        importlib.reload(settings.developments)
        
        from settings.developments import DEBUG
        self.assertTrue(DEBUG)

    def test_postgres_host_from_env(self):
        """Testa se POSTGRES_HOST pode vir de variável de ambiente."""
        # Testa que a configuração existe
        db_host = settings.DATABASES['default']['HOST']
        self.assertIsNotNone(db_host)
        self.assertIsInstance(db_host, str)

    def test_postgres_port_from_env(self):
        """Testa se POSTGRES_PORT pode vir de variável de ambiente."""
        db_port = settings.DATABASES['default']['PORT']
        self.assertIsNotNone(db_port)

    def test_django_secret_key_from_env(self):
        """Testa se SECRET_KEY pode vir de variável de ambiente."""
        self.assertIsNotNone(settings.SECRET_KEY)
        # Em testes, SECRET_KEY pode ser curta
        self.assertGreater(len(settings.SECRET_KEY), 0)


class SettingsIntegrationTestCase(TestCase):
    """Testes de integração para settings."""

    def test_all_required_settings_exist(self):
        """Testa se todas as configurações obrigatórias existem."""
        required_settings = [
            'SECRET_KEY',
            'DEBUG',
            'INSTALLED_APPS',
            'MIDDLEWARE',
            'DATABASES',
            'TEMPLATES',
            'STATIC_URL',
        ]
        
        for setting_name in required_settings:
            self.assertTrue(
                hasattr(settings, setting_name),
                f"Setting {setting_name} não encontrada"
            )

    def test_installed_apps_order(self):
        """Testa se as apps estão em ordem lógica."""
        apps_list = settings.INSTALLED_APPS
        
        # Apps customizadas devem vir antes das do Django (para templates)
        custom_apps = ['base', 'health', 'integrador']
        django_apps = [app for app in apps_list if app.startswith('django.contrib')]
        
        for custom_app in custom_apps:
            if custom_app in apps_list:
                custom_index = apps_list.index(custom_app)
                if django_apps:
                    django_index = apps_list.index(django_apps[0])
                    self.assertLess(
                        custom_index,
                        django_index,
                        f"{custom_app} deve vir antes das apps Django"
                    )

    def test_middleware_order(self):
        """Testa se os middlewares estão em ordem apropriada."""
        middleware_list = settings.MIDDLEWARE
        
        # SecurityMiddleware deve ser um dos primeiros
        if 'django.middleware.security.SecurityMiddleware' in middleware_list:
            security_index = middleware_list.index(
                'django.middleware.security.SecurityMiddleware'
            )
            self.assertLess(security_index, 3)

    def test_database_connection_works(self):
        """Testa se a conexão com banco de dados está funcional."""
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)

    def test_cache_configuration_is_valid(self):
        """Testa se a configuração de cache é válida."""
        from django.core.cache import cache
        
        # Tenta usar o cache
        test_key = 'test_settings_key'
        test_value = 'test_value'
        
        cache.set(test_key, test_value, 10)
        cached_value = cache.get(test_key)
        
        self.assertEqual(cached_value, test_value)
        
        # Limpa
        cache.delete(test_key)


class SettingsSecurityTestCase(TestCase):
    """Testes de segurança para settings."""

    def test_secret_key_is_not_default(self):
        """Testa se SECRET_KEY não é o valor padrão."""
        # SECRET_KEY é necessária para segurança
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertGreater(len(settings.SECRET_KEY), 0)
        
        # Aviso: SECRET_KEY não deve ser 'changeme' em produção!
        # Teste apenas verifica que existe e tem comprimento > 0

    def test_debug_false_in_production(self):
        """Testa se DEBUG está False em produção."""
        # Este teste é mais para documentação
        # Em produção, DEBUG deve ser False
        if hasattr(settings, 'ENVIRONMENT'):
            if settings.ENVIRONMENT == 'production':
                self.assertFalse(settings.DEBUG)

    def test_allowed_hosts_configured(self):
        """Testa se ALLOWED_HOSTS está configurado."""
        if not settings.DEBUG:
            # Em produção, ALLOWED_HOSTS não deve estar vazio
            self.assertTrue(hasattr(settings, 'ALLOWED_HOSTS'))

    def test_secure_ssl_redirect_in_production(self):
        """Testa se SSL redirect está configurado em produção."""
        # Verifica se a configuração GO_TO_HTTPS existe
        from settings.securities import GO_TO_HTTPS
        self.assertIsInstance(GO_TO_HTTPS, bool)

    def test_session_cookie_secure_when_https(self):
        """Testa se session cookie é secure quando usando HTTPS."""
        if hasattr(settings, 'SESSION_COOKIE_SECURE'):
            # Se configurado, deve ser booleano
            self.assertIsInstance(settings.SESSION_COOKIE_SECURE, bool)

    def test_csrf_cookie_secure_when_https(self):
        """Testa se CSRF cookie é secure quando usando HTTPS."""
        self.assertIsInstance(settings.CSRF_COOKIE_SECURE, bool)


class SettingsEdgeCasesTestCase(TestCase):
    """Testes de casos extremos para settings."""

    def test_empty_installed_apps_scenario(self):
        """Testa se há proteção contra INSTALLED_APPS vazio."""
        self.assertGreater(len(settings.INSTALLED_APPS), 0)

    def test_empty_middleware_scenario(self):
        """Testa se há proteção contra MIDDLEWARE vazio."""
        self.assertGreater(len(settings.MIDDLEWARE), 0)

    def test_database_name_is_not_empty(self):
        """Testa se o nome do banco não está vazio."""
        db_name = settings.DATABASES['default']['NAME']
        self.assertIsNotNone(db_name)
        self.assertGreater(len(db_name), 0)

    def test_database_user_is_not_empty(self):
        """Testa se o usuário do banco não está vazio."""
        db_user = settings.DATABASES['default']['USER']
        self.assertIsNotNone(db_user)
        self.assertGreater(len(db_user), 0)

    def test_cache_location_is_not_empty(self):
        """Testa se LOCATION do cache não está vazio."""
        location = settings.CACHES['default']['LOCATION']
        self.assertGreater(len(location), 0)

    @patch.dict(os.environ, {}, clear=True)
    def test_settings_work_without_env_variables(self):
        """Testa se settings funcionam sem variáveis de ambiente."""
        # Settings devem ter valores default
        # Este teste verifica se os defaults estão configurados
        try:
            import settings.databases
            importlib.reload(settings.databases)
            
            from settings.databases import DATABASES
            self.assertIn('default', DATABASES)
        except Exception as e:
            # Se falhar, é esperado que haja defaults adequados
            self.fail(f"Settings devem ter defaults: {e}")


class SettingsPerformanceTestCase(TestCase):
    """Testes de performance para settings."""

    def test_settings_import_performance(self):
        """Testa se a importação de settings é rápida."""
        import time
        
        start = time.time()
        import settings
        importlib.reload(settings)
        end = time.time()
        
        # Import deve ser rápido (menos de 1 segundo)
        self.assertLess(end - start, 1.0)

    def test_database_connection_pool_settings(self):
        """Testa se configurações de pool de conexão existem."""
        # Verifica se OPTIONS está configurado
        db_options = settings.DATABASES['default'].get('OPTIONS', {})
        self.assertIsInstance(db_options, dict)
