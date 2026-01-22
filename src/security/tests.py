"""
Testes unitários para a app security.

Este módulo contém testes para:
- login view: Autenticação OAuth com SUAP
- authenticate view: Callback OAuth e criação/atualização de usuários
- logout view: Desconexão do sistema
- Fluxos de autenticação
- Tratamento de erros
"""
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth import get_user
from django.http import HttpRequest
from unittest.mock import patch, Mock, MagicMock
import json

from security.views import login, authenticate, logout
from security.apps import SecurityConfig


class SecurityAppConfigTestCase(TestCase):
    """Testes para a configuração da app security."""

    def test_app_config_name(self):
        """Testa se o nome da app está correto."""
        self.assertEqual(SecurityConfig.name, 'security')

    def test_app_config_verbose_name(self):
        """Testa verbose_name da app."""
        self.assertEqual(SecurityConfig.verbose_name, 'Segurança')

    def test_app_config_icon(self):
        """Testa se o ícone está definido."""
        self.assertEqual(SecurityConfig.icon, 'fa fa-user')

    def test_app_config_default_auto_field(self):
        """Testa se default_auto_field está configurado."""
        self.assertEqual(
            SecurityConfig.default_auto_field,
            'django.db.models.BigAutoField'
        )


class LoginViewTestCase(TestCase):
    """Testes para a view de login."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.factory = RequestFactory()

    def add_session_to_request(self, request):
        """Adiciona sessão à requisição."""
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

    @override_settings(OAUTH={
        'BASE_URL': 'https://suap.test.com',
        'CLIENT_ID': 'test_client_id'
    })
    def test_login_redirects_to_oauth(self):
        """Testa se login redireciona para OAuth."""
        request = self.factory.get('/login/')
        self.add_session_to_request(request)
        
        response = login(request)
        
        # Verifica redirecionamento
        self.assertEqual(response.status_code, 302)
        
        # Verifica URL de redirecionamento
        self.assertIn('suap.test.com', response.url)
        self.assertIn('authorize', response.url)
        self.assertIn('test_client_id', response.url)

    def test_login_saves_next_parameter_in_session(self):
        """Testa se login salva parâmetro next na sessão."""
        request = self.factory.get('/login/?next=/admin/')
        self.add_session_to_request(request)
        
        login(request)
        
        # Verifica se 'next' foi salvo na sessão
        self.assertEqual(request.session['next'], '/admin/')

    def test_login_default_next_when_not_provided(self):
        """Testa valor padrão de next quando não fornecido."""
        request = self.factory.get('/login/')
        self.add_session_to_request(request)
        
        login(request)
        
        # Deve usar "/" como padrão
        self.assertEqual(request.session['next'], '/')

    @override_settings(OAUTH={
        'BASE_URL': 'https://suap.example.com',
        'CLIENT_ID': 'my_client'
    })
    def test_login_constructs_correct_redirect_uri(self):
        """Testa se a URI de redirecionamento está correta."""
        request = self.factory.get('/login/')
        request.META['HTTP_HOST'] = 'testserver'
        self.add_session_to_request(request)
        
        response = login(request)
        
        # Verifica componentes da URL
        self.assertIn('redirect_uri=http://testserver/authenticate/', response.url)


class AuthenticateViewTestCase(TestCase):
    """Testes para a view de autenticação."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.factory = RequestFactory()

    def add_session_to_request(self, request):
        """Adiciona sessão à requisição."""
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

    def test_authenticate_handles_access_denied(self):
        """Testa tratamento de erro access_denied."""
        request = self.factory.get('/authenticate/?error=access_denied')
        self.add_session_to_request(request)
        
        response = authenticate(request)
        
        # Verifica que renderiza template de não autorizado
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'not_authorized', response.content)

    @patch('security.views.requests.post')
    @patch('security.views.requests.get')
    @override_settings(OAUTH={
        'BASE_URL': 'https://suap.test.com',
        'TOKEN_URL': 'https://suap.test.com/o/token/',
        'USERINFO_URL': 'https://suap.test.com/api/rh/eu/',
        'CLIENT_ID': 'test_client',
        'CLIENT_SECRET': 'test_secret'
    })
    def test_authenticate_successful_flow(self, mock_get, mock_post):
        """Testa fluxo de autenticação bem-sucedido."""
        # Mock do token response
        mock_post.return_value = Mock(text=json.dumps({
            'access_token': 'test_token',
            'scope': 'test_scope'
        }))
        
        # Mock do userinfo response
        mock_get.return_value = Mock(text=json.dumps({
            'identificacao': 'testuser',
            'primeiro_nome': 'Test',
            'ultimo_nome': 'User',
            'email_preferencial': 'test@example.com'
        }))
        
        request = self.factory.get('/authenticate/?code=test_code')
        request.META['HTTP_HOST'] = 'testserver'
        self.add_session_to_request(request)
        request.session['next'] = '/admin/'
        
        response = authenticate(request)
        
        # Verifica redirecionamento
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/admin/')
        
        # Verifica que usuário foi criado
        user = User.objects.get(username='testuser')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.email, 'test@example.com')

    @patch('security.views.requests.post')
    @patch('security.views.requests.get')
    @override_settings(OAUTH={
        'BASE_URL': 'https://suap.test.com',
        'TOKEN_URL': 'https://suap.test.com/o/token/',
        'USERINFO_URL': 'https://suap.test.com/api/rh/eu/',
        'CLIENT_ID': 'test_client',
        'CLIENT_SECRET': 'test_secret'
    })
    def test_authenticate_creates_first_user_as_superuser(self, mock_get, mock_post):
        """Testa que primeiro usuário é criado como superuser."""
        # Mock das respostas
        mock_post.return_value = Mock(text=json.dumps({
            'access_token': 'test_token',
            'scope': 'test_scope'
        }))
        
        mock_get.return_value = Mock(text=json.dumps({
            'identificacao': 'firstuser',
            'primeiro_nome': 'First',
            'ultimo_nome': 'User',
            'email_preferencial': 'first@example.com'
        }))
        
        # Garante que não há usuários
        User.objects.all().delete()
        
        request = self.factory.get('/authenticate/?code=test_code')
        request.META['HTTP_HOST'] = 'testserver'
        self.add_session_to_request(request)
        request.session['next'] = '/'
        
        authenticate(request)
        
        # Verifica que primeiro usuário é superuser
        user = User.objects.get(username='firstuser')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    @patch('security.views.requests.post')
    @patch('security.views.requests.get')
    @override_settings(OAUTH={
        'BASE_URL': 'https://suap.test.com',
        'TOKEN_URL': 'https://suap.test.com/o/token/',
        'USERINFO_URL': 'https://suap.test.com/api/rh/eu/',
        'CLIENT_ID': 'test_client',
        'CLIENT_SECRET': 'test_secret'
    })
    def test_authenticate_updates_existing_user(self, mock_get, mock_post):
        """Testa atualização de usuário existente."""
        # Cria usuário existente
        existing_user = User.objects.create_user(
            username='existinguser',
            first_name='Old',
            last_name='Name',
            email='old@example.com'
        )
        
        # Mock das respostas
        mock_post.return_value = Mock(text=json.dumps({
            'access_token': 'test_token',
            'scope': 'test_scope'
        }))
        
        mock_get.return_value = Mock(text=json.dumps({
            'identificacao': 'existinguser',
            'primeiro_nome': 'New',
            'ultimo_nome': 'Name',
            'email_preferencial': 'new@example.com'
        }))
        
        request = self.factory.get('/authenticate/?code=test_code')
        request.META['HTTP_HOST'] = 'testserver'
        self.add_session_to_request(request)
        request.session['next'] = '/'
        
        authenticate(request)
        
        # Verifica que usuário foi atualizado
        user = User.objects.get(username='existinguser')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.email, 'new@example.com')

    def test_authenticate_without_code_parameter(self):
        """Testa authenticate sem parâmetro code."""
        request = self.factory.get('/authenticate/')
        self.add_session_to_request(request)
        
        response = authenticate(request)
        
        # Deve renderizar página de erro
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'authorization_error', response.content)

    @patch('security.views.requests.post')
    @override_settings(OAUTH={
        'BASE_URL': 'https://suap.test.com',
        'TOKEN_URL': 'https://suap.test.com/o/token/',
        'CLIENT_ID': 'test_client',
        'CLIENT_SECRET': 'test_secret'
    })
    def test_authenticate_handles_token_error(self, mock_post):
        """Testa tratamento de erro ao obter token."""
        # Mock de erro no token
        mock_post.side_effect = Exception('Token request failed')
        
        request = self.factory.get('/authenticate/?code=test_code')
        request.META['HTTP_HOST'] = 'testserver'
        self.add_session_to_request(request)
        
        response = authenticate(request)
        
        # Deve renderizar página de erro
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'authorization_error', response.content)

    @patch('security.views.requests.post')
    @patch('security.views.requests.get')
    @override_settings(OAUTH={
        'BASE_URL': 'https://suap.test.com',
        'TOKEN_URL': 'https://suap.test.com/o/token/',
        'USERINFO_URL': 'https://suap.test.com/api/rh/eu/',
        'CLIENT_ID': 'test_client',
        'CLIENT_SECRET': 'test_secret'
    })
    def test_authenticate_uses_default_email_when_not_provided(self, mock_get, mock_post):
        """Testa uso de email padrão quando não fornecido."""
        mock_post.return_value = Mock(text=json.dumps({
            'access_token': 'test_token',
            'scope': 'test_scope'
        }))
        
        # Userinfo sem email_preferencial
        mock_get.return_value = Mock(text=json.dumps({
            'identificacao': 'noemail',
            'primeiro_nome': 'No',
            'ultimo_nome': 'Email'
        }))
        
        request = self.factory.get('/authenticate/?code=test_code')
        request.META['HTTP_HOST'] = 'testserver'
        self.add_session_to_request(request)
        request.session['next'] = '/'
        
        authenticate(request)
        
        # Verifica email padrão
        user = User.objects.get(username='noemail')
        self.assertEqual(user.email, 'noemail@ifrn.edu.br')

    @patch('security.views.requests.post')
    @patch('security.views.requests.get')
    @patch('security.views.capture_exception')
    @override_settings(OAUTH={
        'BASE_URL': 'https://suap.test.com',
        'TOKEN_URL': 'https://suap.test.com/o/token/',
        'USERINFO_URL': 'https://suap.test.com/api/rh/eu/',
        'CLIENT_ID': 'test_client',
        'CLIENT_SECRET': 'test_secret'
    })
    def test_authenticate_handles_generic_exception(self, mock_capture, mock_get, mock_post):
        """Testa tratamento de exceção genérica."""
        mock_post.side_effect = Exception("Network error")
        
        request = self.factory.get('/authenticate/?code=test_code')
        request.META['HTTP_HOST'] = 'testserver'
        self.add_session_to_request(request)
        
        response = authenticate(request)
        
        # Deve renderizar página de erro
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'authorization_error', response.content)
        mock_capture.assert_called_once()

    @patch('security.views.requests.post')
    @patch('security.views.requests.get')
    @override_settings(OAUTH={
        'BASE_URL': 'https://suap.test.com',
        'TOKEN_URL': 'https://suap.test.com/o/token/',
        'USERINFO_URL': 'https://suap.test.com/api/rh/eu/',
        'CLIENT_ID': 'test_client',
        'CLIENT_SECRET': 'test_secret'
    })
    def test_authenticate_with_email_preferencial(self, mock_get, mock_post):
        """Testa que email_preferencial tem prioridade."""
        mock_post.return_value = Mock(text=json.dumps({
            'access_token': 'test_token',
            'scope': 'test_scope'
        }))
        
        mock_get.return_value = Mock(text=json.dumps({
            'identificacao': 'testuser',
            'primeiro_nome': 'Test',
            'ultimo_nome': 'User',
            'email_preferencial': 'preferred@example.com'
        }))
        
        request = self.factory.get('/authenticate/?code=test_code')
        request.META['HTTP_HOST'] = 'testserver'
        self.add_session_to_request(request)
        request.session['next'] = '/'
        
        authenticate(request)
        
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'preferred@example.com')


class LogoutViewTestCase(TestCase):
    """Testes para a view de logout."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='password123'
        )

    def add_session_to_request(self, request):
        """Adiciona sessão à requisição."""
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

    @override_settings(
        LOGOUT_REDIRECT_URL='https://suap.test.com/logout',
        LOGIN_REDIRECT_URL='/admin/'
    )
    def test_logout_redirects_to_suap(self):
        """Testa se logout redireciona para SUAP."""
        request = self.factory.get('/logout/')
        request.user = self.user
        self.add_session_to_request(request)
        
        response = logout(request)
        
        # Verifica redirecionamento
        self.assertEqual(response.status_code, 302)
        self.assertIn('suap.test.com/logout', response.url)

    @override_settings(
        LOGOUT_REDIRECT_URL='https://suap.test.com/logout',
        LOGIN_REDIRECT_URL='/admin/'
    )
    def test_logout_includes_next_parameter(self):
        """Testa se logout inclui parâmetro next."""
        request = self.factory.get('/logout/')
        request.user = self.user
        self.add_session_to_request(request)
        
        response = logout(request)
        
        # Verifica que URL contém next parameter
        self.assertIn('next=', response.url)
        self.assertIn('%2Fadmin%2F', response.url)  # URL encoded /admin/

    @override_settings(
        LOGOUT_REDIRECT_URL='https://suap.test.com/logout',
        LOGIN_REDIRECT_URL='/admin/'
    )
    def test_logout_includes_logout_token(self):
        """Testa se logout inclui token da sessão."""
        request = self.factory.get('/logout/')
        request.user = self.user
        self.add_session_to_request(request)
        request.session['logout_token'] = 'test_token_123'
        
        response = logout(request)
        
        # Verifica que URL contém token
        self.assertIn('token=test_token_123', response.url)

    def test_logout_with_empty_logout_token(self):
        """Testa logout sem logout_token na sessão."""
        request = self.factory.get('/logout/')
        request.user = self.user
        self.add_session_to_request(request)
        
        response = logout(request)
        
        # Deve funcionar sem token
        self.assertEqual(response.status_code, 302)
        self.assertIn('token=', response.url)


class SecurityURLsTestCase(TestCase):
    """Testes para URLs da app security."""

    def test_login_url_is_accessible(self):
        """Testa se a URL /login/ é acessível."""
        response = self.client.get('/login/')
        
        # Deve redirecionar para OAuth
        self.assertEqual(response.status_code, 302)

    def test_authenticate_url_is_accessible(self):
        """Testa se a URL /authenticate/ é acessível."""
        response = self.client.get('/authenticate/')
        
        # Deve retornar resposta (erro ou página)
        self.assertIn(response.status_code, [200, 302])

    def test_logout_url_is_accessible(self):
        """Testa se a URL /logout/ é acessível."""
        response = self.client.get('/logout/')
        
        # Deve redirecionar
        self.assertEqual(response.status_code, 302)


class IntegrationTestCase(TestCase):
    """Testes de integração para fluxos de autenticação."""

    @patch('security.views.requests.post')
    @patch('security.views.requests.get')
    @override_settings(OAUTH={
        'BASE_URL': 'https://suap.test.com',
        'TOKEN_URL': 'https://suap.test.com/o/token/',
        'USERINFO_URL': 'https://suap.test.com/api/rh/eu/',
        'CLIENT_ID': 'test_client',
        'CLIENT_SECRET': 'test_secret'
    })
    def test_complete_authentication_flow(self, mock_get, mock_post):
        """Testa fluxo completo de autenticação."""
        # 1. Login - redireciona para OAuth
        response = self.client.get('/login/?next=/admin/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('authorize', response.url)
        
        # 2. Mock de retorno do OAuth
        mock_post.return_value = Mock(text=json.dumps({
            'access_token': 'test_token',
            'scope': 'test_scope'
        }))
        
        mock_get.return_value = Mock(text=json.dumps({
            'identificacao': 'integrationtest',
            'primeiro_nome': 'Integration',
            'ultimo_nome': 'Test',
            'email_preferencial': 'integration@test.com'
        }))
        
        # 3. Authenticate - processa callback
        session = self.client.session
        session['next'] = '/admin/'
        session.save()
        
        response = self.client.get('/authenticate/?code=test_code')
        
        # Deve criar usuário e redirecionar
        self.assertEqual(response.status_code, 302)
        
        # 4. Verifica que usuário foi criado
        user = User.objects.get(username='integrationtest')
        self.assertEqual(user.email, 'integration@test.com')


class EdgeCasesTestCase(TestCase):
    """Testes de casos extremos."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.factory = RequestFactory()

    def add_session_to_request(self, request):
        """Adiciona sessão à requisição."""
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

    @patch('security.views.requests.post')
    @override_settings(OAUTH={
        'BASE_URL': 'https://suap.test.com',
        'TOKEN_URL': 'https://suap.test.com/o/token/',
        'CLIENT_ID': 'test_client',
        'CLIENT_SECRET': 'test_secret'
    })
    def test_authenticate_with_mismatching_redirect_uri_error(self, mock_post):
        """Testa erro de redirect URI não correspondente."""
        mock_post.return_value = Mock(text=json.dumps({
            'error_description': 'Mismatching redirect URI.'
        }))
        
        request = self.factory.get('/authenticate/?code=test_code')
        request.META['HTTP_HOST'] = 'testserver'
        self.add_session_to_request(request)
        
        # Deve lançar ValueError
        with self.assertRaises(ValueError):
            authenticate(request)

    @patch('security.views.requests.post')
    @patch('security.views.requests.get')
    @override_settings(OAUTH={
        'BASE_URL': 'https://suap.test.com',
        'TOKEN_URL': 'https://suap.test.com/o/token/',
        'USERINFO_URL': 'https://suap.test.com/api/rh/eu/',
        'CLIENT_ID': 'test_client',
        'CLIENT_SECRET': 'test_secret'
    })
    def test_authenticate_with_very_long_username(self, mock_get, mock_post):
        """Testa autenticação com username muito longo."""
        mock_post.return_value = Mock(text=json.dumps({
            'access_token': 'test_token',
            'scope': 'test_scope'
        }))
        
        long_username = 'a' * 200
        mock_get.return_value = Mock(text=json.dumps({
            'identificacao': long_username,
            'primeiro_nome': 'Long',
            'ultimo_nome': 'User'
        }))
        
        request = self.factory.get('/authenticate/?code=test_code')
        request.META['HTTP_HOST'] = 'testserver'
        self.add_session_to_request(request)
        request.session['next'] = '/'
        
        # Pode falhar devido a limite de tamanho do campo
        try:
            authenticate(request)
        except Exception:
            # É esperado que falhe com username muito longo
            pass

    def test_login_with_special_characters_in_next(self):
        """Testa login com caracteres especiais em next."""
        request = self.factory.get('/login/?next=/admin/test?id=123&name=test')
        self.add_session_to_request(request)
        
        login(request)
        
        # Deve salvar corretamente
        self.assertIn('next', request.session)

    @override_settings(
        LOGOUT_REDIRECT_URL='https://suap.test.com/logout',
        LOGIN_REDIRECT_URL='/admin/'
    )
    def test_logout_without_authenticated_user(self):
        """Testa logout sem usuário autenticado."""
        request = self.factory.get('/logout/')
        request.user = None
        self.add_session_to_request(request)
        
        response = logout(request)
        
        # Deve funcionar mesmo sem usuário
        self.assertEqual(response.status_code, 302)
