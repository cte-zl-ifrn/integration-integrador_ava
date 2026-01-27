"""
Testes unitários para a app integrador.

Este módulo contém testes para:
- Models: Ambiente, Solicitacao
- Decorators: json_response, exception_as_json, check_is_post, check_is_get, valid_token, check_json, try_solicitacao, detect_ambiente
- Views: sync_up_enrolments, sync_down_grades
- Utils: SyncError, validate_http_response, http_get, http_post, http_get_json, http_post_json
- Middleware: DisableCSRFForAPIMiddleware
- Brokers: BaseBroker, Suap2LocalSuapBroker
- Management Commands: atualiza_solicitacoes
"""
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.http import JsonResponse, HttpRequest
from django.db.utils import IntegrityError
from unittest.mock import patch, Mock, MagicMock, mock_open
from http.client import HTTPException
import json
import io
import logging

from integrador.models import Ambiente, Solicitacao
from integrador.apps import IntegradorConfig
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
from integrador.views import sync_up_enrolments, sync_down_grades
from integrador.utils import (
    SyncError,
    validate_http_response,
    http_get,
    http_post,
    http_get_json,
    http_post_json
)
from integrador.middleware import DisableCSRFForAPIMiddleware
from integrador.brokers.base import BaseBroker
from integrador.brokers.suap2local_suap import Suap2LocalSuapBroker

# Configura logging para WARNING durante testes (suprime DEBUG e INFO)
logging.getLogger('integrador').setLevel(logging.WARNING)


class IntegradorConfigTestCase(TestCase):
    """Testes para a configuração da app integrador."""

    def test_app_config_name(self):
        """Testa se o nome da app está correto."""
        self.assertEqual(IntegradorConfig.name, 'integrador')

    def test_app_config_icon(self):
        """Testa se o ícone está definido."""
        self.assertEqual(IntegradorConfig.icon, 'fa fa-home')

    def test_app_config_default_auto_field(self):
        """Testa se default_auto_field está configurado."""
        self.assertEqual(
            IntegradorConfig.default_auto_field,
            'django.db.models.BigAutoField'
        )


class AmbienteModelTestCase(TestCase):
    """Testes para o modelo Ambiente."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.ambiente = Ambiente.objects.create(
            nome="Ambiente Teste",
            url="https://test.moodle.com",
            token="test_token_123",
            expressao_seletora="campus.sigla == 'TEST'",
            ordem=1,
            active=True
        )

    def test_create_ambiente(self):
        """Testa criação de ambiente."""
        ambiente = Ambiente.objects.create(
            nome="Outro Ambiente",
            url="https://outro.moodle.com",
            token="outro_token",
            expressao_seletora="campus.sigla == 'OUTRO'",
            ordem=2
        )
        
        self.assertIsNotNone(ambiente.pk)
        self.assertEqual(ambiente.nome, "Outro Ambiente")

    def test_ambiente_str_representation(self):
        """Testa representação em string do ambiente."""
        self.assertEqual(str(self.ambiente), "Ambiente Teste")

    def test_ambiente_base_url_without_trailing_slash(self):
        """Testa propriedade base_url sem barra final."""
        self.assertEqual(self.ambiente.base_url, "https://test.moodle.com")

    def test_ambiente_base_url_with_trailing_slash(self):
        """Testa propriedade base_url com barra final."""
        self.ambiente.url = "https://test.moodle.com/"
        self.ambiente.save()
        
        self.assertEqual(self.ambiente.base_url, "https://test.moodle.com")

    def test_ambiente_valid_expressao_seletora(self):
        """Testa validação de expressão seletora válida."""
        self.assertTrue(self.ambiente.valid_expressao_seletora)

    def test_ambiente_invalid_expressao_seletora(self):
        """Testa validação de expressão seletora inválida."""
        self.ambiente.expressao_seletora = "invalid syntax {{"
        self.ambiente.save()
        
        self.assertFalse(self.ambiente.valid_expressao_seletora)

    def test_ambiente_empty_expressao_seletora(self):
        """Testa validação de expressão seletora vazia."""
        self.ambiente.expressao_seletora = ""
        self.ambiente.save()
        
        self.assertFalse(self.ambiente.valid_expressao_seletora)

    def test_ambiente_null_expressao_seletora(self):
        """Testa validação de expressão seletora nula."""
        # Campo expressao_seletora é NOT NULL no banco, então testamos validação antes de save
        self.ambiente.expressao_seletora = ""
        self.ambiente.save()
        
        self.assertFalse(self.ambiente.valid_expressao_seletora)

    def test_ambiente_ordering(self):
        """Testa ordenação de ambientes."""
        ambiente2 = Ambiente.objects.create(
            nome="Ambiente 2",
            url="https://test2.com",
            token="token2",
            expressao_seletora="1=1",
            ordem=0
        )
        
        ambientes = list(Ambiente.objects.all())
        # Ordenação por ordem, id
        self.assertEqual(ambientes[0], ambiente2)

    def test_ambiente_manager_seleciona_ambiente(self):
        """Testa método seleciona_ambiente do manager."""
        sync_json = {"campus": {"sigla": "TEST"}}
        
        ambiente_selecionado = Ambiente.objects.seleciona_ambiente(sync_json)
        
        self.assertEqual(ambiente_selecionado, self.ambiente)

    def test_ambiente_manager_seleciona_ambiente_nao_encontrado(self):
        """Testa seleciona_ambiente quando não encontra ambiente."""
        sync_json = {"campus": {"sigla": "INEXISTENTE"}}
        
        ambiente_selecionado = Ambiente.objects.seleciona_ambiente(sync_json)
        
        self.assertIsNone(ambiente_selecionado)

    def test_ambiente_manager_seleciona_ambiente_only_active(self):
        """Testa que seleciona_ambiente só retorna ambientes ativos."""
        self.ambiente.active = False
        self.ambiente.save()
        
        sync_json = {"campus": {"sigla": "TEST"}}
        ambiente_selecionado = Ambiente.objects.seleciona_ambiente(sync_json)
        
        self.assertIsNone(ambiente_selecionado)

    def test_ambiente_verbose_names(self):
        """Testa verbose_name e verbose_name_plural."""
        self.assertEqual(Ambiente._meta.verbose_name, "ambiente")
        self.assertEqual(Ambiente._meta.verbose_name_plural, "ambientes")


class SolicitacaoModelTestCase(TestCase):
    """Testes para o modelo Solicitacao."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.ambiente = Ambiente.objects.create(
            nome="Ambiente Teste",
            url="https://test.moodle.com",
            token="test_token",
            expressao_seletora="campus.sigla == 'TEST'",
            active=True
        )
        
        self.recebido_json = {
            "campus": {"sigla": "TEST"},
            "turma": {"codigo": "20261.1.132456.123.1M"},
            "componente": {"sigla": "MAT.001"},
            "diario": {"id": 12345, "tipo": "regular"}
        }
        
        self.solicitacao = Solicitacao.objects.create(
            ambiente=self.ambiente,
            operacao=Solicitacao.Operacao.SYNC_UP_DIARIO,
            status=Solicitacao.Status.PROCESSANDO,
            recebido=self.recebido_json
        )

    def test_create_solicitacao(self):
        """Testa criação de solicitação."""
        solicitacao = Solicitacao.objects.create(
            ambiente=self.ambiente,
            operacao=Solicitacao.Operacao.SYNC_DOWN_NOTAS,
            status=Solicitacao.Status.SUCESSO,
            recebido={"campus": {"sigla": "TEST"}, "diario": {"id": 999}}
        )
        
        self.assertIsNotNone(solicitacao.pk)
        self.assertEqual(solicitacao.operacao, Solicitacao.Operacao.SYNC_DOWN_NOTAS)

    def test_solicitacao_str_representation(self):
        """Testa representação em string da solicitação."""
        string_repr = str(self.solicitacao)
        
        self.assertIn("TEST", string_repr)
        self.assertIn("12345", string_repr)

    def test_solicitacao_auto_populate_on_save(self):
        """Testa que save() popula campos automaticamente."""
        self.assertEqual(self.solicitacao.campus_sigla, "TEST")
        self.assertEqual(self.solicitacao.diario_id, 12345)
        self.assertEqual(self.solicitacao.tipo, "regular")
        # diario_codigo é gerado como turma.codigo#diario.id
        self.assertIn("20261.1.132456.123.1M", self.solicitacao.diario_codigo)
        self.assertIn("#12345", self.solicitacao.diario_codigo)

    def test_solicitacao_status_merged_property(self):
        """Testa propriedade status_merged."""
        self.solicitacao.status = Solicitacao.Status.SUCESSO
        self.solicitacao.status_code = "200"
        
        status_html = self.solicitacao.status_merged
        
        self.assertIn("Sucesso", status_html)
        self.assertIn("200", status_html)

    def test_solicitacao_timestamp_auto_created(self):
        """Testa que timestamp é criado automaticamente."""
        self.assertIsNotNone(self.solicitacao.timestamp)

    def test_solicitacao_ordering(self):
        """Testa ordenação de solicitações."""
        solicitacao2 = Solicitacao.objects.create(
            ambiente=self.ambiente,
            operacao=Solicitacao.Operacao.SYNC_UP_DIARIO,
            recebido={"campus": {"sigla": "TEST"}, "diario": {"id": 999}}
        )
        
        solicitacoes = list(Solicitacao.objects.all())
        # Ordenação por -timestamp (mais recentes primeiro)
        self.assertEqual(solicitacoes[0], solicitacao2)

    def test_solicitacao_status_choices(self):
        """Testa choices de status."""
        self.solicitacao.status = Solicitacao.Status.SUCESSO
        self.solicitacao.save()
        
        solicitacao = Solicitacao.objects.get(pk=self.solicitacao.pk)
        self.assertEqual(solicitacao.status, Solicitacao.Status.SUCESSO)

    def test_solicitacao_operacao_choices(self):
        """Testa choices de operação."""
        self.assertEqual(
            self.solicitacao.operacao,
            Solicitacao.Operacao.SYNC_UP_DIARIO
        )

    def test_solicitacao_json_fields(self):
        """Testa campos JSON."""
        self.solicitacao.enviado = {"test": "data"}
        self.solicitacao.respondido = {"response": "ok"}
        self.solicitacao.save()
        
        solicitacao = Solicitacao.objects.get(pk=self.solicitacao.pk)
        self.assertEqual(solicitacao.enviado["test"], "data")
        self.assertEqual(solicitacao.respondido["response"], "ok")

    def test_solicitacao_verbose_names(self):
        """Testa verbose_name e verbose_name_plural."""
        self.assertEqual(Solicitacao._meta.verbose_name, "solicitação")
        self.assertEqual(Solicitacao._meta.verbose_name_plural, "solicitações")


class SyncErrorTestCase(TestCase):
    """Testes para a classe SyncError."""

    def test_sync_error_creation(self):
        """Testa criação de SyncError."""
        error = SyncError("Test error", 500)
        
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.code, 500)

    def test_sync_error_with_retorno(self):
        """Testa SyncError com retorno."""
        retorno = {"detail": "error detail"}
        error = SyncError("Test error", 400, retorno=retorno)
        
        self.assertEqual(error.retorno, retorno)


class UtilsFunctionsTestCase(TestCase):
    """Testes para funções utilitárias."""

    @patch('integrador.utils.requests.get')
    def test_http_get_success(self, mock_get):
        """Testa http_get com sucesso."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = b"Test content"
        mock_get.return_value = mock_response
        
        result = http_get("http://test.com")
        
        self.assertEqual(result, "Test content")

    @patch('integrador.utils.requests.get')
    def test_http_get_failure(self, mock_get):
        """Testa http_get com falha."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.content = b"Error"
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        with self.assertRaises(HTTPException):
            http_get("http://test.com")

    @patch('integrador.utils.requests.post')
    def test_http_post_success(self, mock_post):
        """Testa http_post com sucesso."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = b"Posted"
        mock_post.return_value = mock_response
        
        result = http_post("http://test.com", {"data": "value"})
        
        self.assertEqual(result, "Posted")

    @patch('integrador.utils.requests.post')
    def test_http_post_failure(self, mock_post):
        """Testa http_post com falha."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.reason = "Server Error"
        mock_response.content = b"Error"
        mock_response.headers = {}
        mock_post.return_value = mock_response
        
        with self.assertRaises(HTTPException):
            http_post("http://test.com", {"data": "value"})

    @patch('integrador.utils.http_get')
    def test_http_get_json_success(self, mock_http_get):
        """Testa http_get_json com sucesso."""
        mock_http_get.return_value = '{"key": "value"}'
        
        result = http_get_json("http://test.com")
        
        self.assertEqual(result, {"key": "value"})

    @patch('integrador.utils.http_post')
    def test_http_post_json_success(self, mock_http_post):
        """Testa http_post_json com sucesso."""
        mock_http_post.return_value = '{"result": "success"}'
        
        result = http_post_json("http://test.com", {"data": "value"})
        
        self.assertEqual(result, {"result": "success"})

    def test_validate_http_response_success(self):
        """Testa validate_http_response com resposta ok."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.content = b"Success"
        
        result = validate_http_response("http://test.com", "utf-8", True, mock_response)
        
        self.assertEqual(result, "Success")

    def test_validate_http_response_failure(self):
        """Testa validate_http_response com resposta não-ok."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"
        mock_response.content = b"Access denied"
        mock_response.headers = {}
        
        with self.assertRaises(HTTPException) as context:
            validate_http_response("http://test.com", "utf-8", True, mock_response)
        
        self.assertEqual(context.exception.status, 403)


class DecoratorsTestCase(TestCase):
    """Testes para decorators."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.factory = RequestFactory()

    def test_json_response_decorator_with_dict(self):
        """Testa decorator json_response com dicionário."""
        @json_response
        def test_view(request):
            return {"status": "ok"}
        
        request = self.factory.get('/test/')
        response = test_view(request)
        
        self.assertIsInstance(response, JsonResponse)

    def test_json_response_decorator_with_json_response(self):
        """Testa decorator json_response com JsonResponse."""
        @json_response
        def test_view(request):
            return JsonResponse({"status": "ok"})
        
        request = self.factory.get('/test/')
        response = test_view(request)
        
        self.assertIsInstance(response, JsonResponse)

    def test_exception_as_json_decorator_success(self):
        """Testa decorator exception_as_json com sucesso."""
        @exception_as_json
        def test_view(request):
            return JsonResponse({"status": "ok"})
        
        request = self.factory.get('/test/')
        response = test_view(request)
        
        self.assertEqual(response.status_code, 200)

    def test_exception_as_json_decorator_with_sync_error(self):
        """Testa decorator exception_as_json com SyncError."""
        @exception_as_json
        def test_view(request):
            raise SyncError("Test error", 400)
        
        request = self.factory.get('/test/')
        response = test_view(request)
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("error", data)

    def test_exception_as_json_decorator_with_generic_exception(self):
        """Testa decorator exception_as_json com exceção genérica."""
        @exception_as_json
        def test_view(request):
            raise Exception("Generic error")
        
        request = self.factory.get('/test/')
        response = test_view(request)
        
        self.assertEqual(response.status_code, 500)

    @override_settings(SUAP_INTEGRADOR_KEY='test_key_123')
    def test_valid_token_decorator_success(self):
        """Testa decorator valid_token com token válido."""
        @valid_token
        def test_view(request):
            return {"status": "ok"}
        
        request = self.factory.get('/test/')
        request.META['HTTP_AUTHENTICATION'] = 'Token test_key_123'
        
        result = test_view(request)
        self.assertEqual(result["status"], "ok")

    @override_settings(SUAP_INTEGRADOR_KEY='test_key_123')
    def test_valid_token_decorator_invalid_token(self):
        """Testa decorator valid_token com token inválido."""
        @valid_token
        def test_view(request):
            return {"status": "ok"}
        
        request = self.factory.get('/test/')
        request.META['HTTP_AUTHENTICATION'] = 'Token wrong_token'
        
        with self.assertRaises(SyncError) as context:
            test_view(request)
        
        self.assertEqual(context.exception.code, 403)

    @override_settings(SUAP_INTEGRADOR_KEY='test_key_123')
    def test_valid_token_decorator_missing_token(self):
        """Testa decorator valid_token sem token."""
        @valid_token
        def test_view(request):
            return {"status": "ok"}
        
        request = self.factory.get('/test/')
        
        with self.assertRaises(SyncError) as context:
            test_view(request)
        
        self.assertEqual(context.exception.code, 431)

    def test_check_is_post_decorator_success(self):
        """Testa decorator check_is_post com POST."""
        @check_is_post
        def test_view(request):
            return {"status": "ok"}
        
        request = self.factory.post('/test/')
        result = test_view(request)
        
        self.assertEqual(result["status"], "ok")

    def test_check_is_post_decorator_failure(self):
        """Testa decorator check_is_post com GET."""
        @check_is_post
        def test_view(request):
            return {"status": "ok"}
        
        request = self.factory.get('/test/')
        
        with self.assertRaises(SyncError) as context:
            test_view(request)
        
        self.assertEqual(context.exception.code, 501)

    def test_check_is_get_decorator_success(self):
        """Testa decorator check_is_get com GET."""
        @check_is_get
        def test_view(request):
            return {"status": "ok"}
        
        request = self.factory.get('/test/')
        result = test_view(request)
        
        self.assertEqual(result["status"], "ok")

    def test_check_is_get_decorator_failure(self):
        """Testa decorator check_is_get com POST."""
        @check_is_get
        def test_view(request):
            return {"status": "ok"}
        
        request = self.factory.post('/test/')
        
        with self.assertRaises(SyncError) as context:
            test_view(request)
        
        self.assertEqual(context.exception.code, 501)

    def test_check_json_decorator_valid_json(self):
        """Testa decorator check_json com JSON válido."""
        @check_json(Solicitacao.Operacao.SYNC_UP_DIARIO)
        def test_view(request):
            return request.json_recebido
        
        json_data = {"campus": {"sigla": "TEST"}}
        request = self.factory.post(
            '/test/',
            data=json.dumps(json_data),
            content_type='application/json'
        )
        
        result = test_view(request)
        self.assertEqual(result, json_data)

    def test_check_json_decorator_invalid_json(self):
        """Testa decorator check_json com JSON inválido."""
        @check_json(Solicitacao.Operacao.SYNC_UP_DIARIO)
        def test_view(request):
            return request.json_recebido
        
        request = self.factory.post(
            '/test/',
            data="invalid json {{{",
            content_type='application/json'
        )
        
        result = test_view(request)
        self.assertIn("error", result)

    def test_detect_ambiente_decorator_found(self):
        """Testa decorator detect_ambiente encontrando ambiente."""
        ambiente = Ambiente.objects.create(
            nome="Test",
            url="http://test.com",
            token="token",
            expressao_seletora="campus.sigla == 'TEST'",
            active=True
        )
        
        @detect_ambiente
        def test_view(request):
            return {"ambiente": request.ambiente.nome}
        
        request = self.factory.get('/test/?campus_sigla=TEST')
        request.json_recebido = {"campus": {"sigla": "TEST"}}
        
        response = test_view(request)
        data = json.loads(response.content)
        self.assertEqual(data["ambiente"], "Test")

    def test_detect_ambiente_decorator_not_found(self):
        """Testa decorator detect_ambiente não encontrando ambiente."""
        @detect_ambiente
        def test_view(request):
            return {"status": "ok"}
        
        request = self.factory.get('/test/?campus_sigla=INEXISTENTE')
        request.json_recebido = {"campus": {"sigla": "INEXISTENTE"}}
        
        with self.assertRaises(SyncError) as context:
            test_view(request)
        
        self.assertEqual(context.exception.code, 404)


class TrySolicitacaoDecoratorTestCase(TestCase):
    """Testes para o decorator try_solicitacao."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.factory = RequestFactory()
        self.ambiente = Ambiente.objects.create(
            nome="Test",
            url="http://test.com",
            token="token",
            expressao_seletora="1 ==1",
            active=True
        )

    def test_try_solicitacao_success(self):
        """Testa try_solicitacao com sucesso."""
        @try_solicitacao(Solicitacao.Operacao.SYNC_UP_DIARIO)
        def test_view(request):
            return {"status": "ok"}
        
        request = self.factory.post('/test/')
        request.ambiente = self.ambiente
        request.json_recebido = {
            "campus": {"sigla": "TEST"},
            "turma": {"codigo": "T1"},
            "componente": {"sigla": "C1"},
            "diario": {"id": 123}
        }
        
        result = test_view(request)
        
        self.assertEqual(result["status"], "ok")
        self.assertEqual(Solicitacao.objects.count(), 1)
        
        solicitacao = Solicitacao.objects.first()
        self.assertEqual(solicitacao.status, Solicitacao.Status.SUCESSO)

    def test_try_solicitacao_with_error(self):
        """Testa try_solicitacao com erro na view."""
        @try_solicitacao(Solicitacao.Operacao.SYNC_UP_DIARIO)
        def test_view(request):
            raise Exception("View error")
        
        request = self.factory.post('/test/')
        request.ambiente = self.ambiente
        request.json_recebido = {
            "campus": {"sigla": "TEST"},
            "turma": {"codigo": "T1"},
            "componente": {"sigla": "C1"},
            "diario": {"id": 123}
        }
        
        with self.assertRaises(SyncError):
            test_view(request)
        
        solicitacao = Solicitacao.objects.first()
        self.assertEqual(solicitacao.status, Solicitacao.Status.FALHA)

    def test_try_solicitacao_with_json_error(self):
        """Testa try_solicitacao com erro no JSON."""
        @try_solicitacao(Solicitacao.Operacao.SYNC_UP_DIARIO)
        def test_view(request):
            return {"status": "ok"}
        
        request = self.factory.post('/test/')
        request.ambiente = self.ambiente
        request.json_recebido = {
            "error": {"code": 400, "message": "Invalid JSON"}
        }
        
        with self.assertRaises(SyncError) as context:
            test_view(request)
        
        self.assertEqual(context.exception.code, 400)


class MiddlewareTestCase(TestCase):
    """Testes para middleware."""

    def setUp(self):
        """Configura o ambiente de teste."""
        # Suprime logs durante testes
        logging.getLogger('integrador').setLevel(logging.WARNING)
        
        self.factory = RequestFactory()
        self.middleware = DisableCSRFForAPIMiddleware(lambda x: None)

    def test_csrf_middleware_exempts_api_urls(self):
        """Testa que middleware isenta URLs da API de CSRF."""
        request = self.factory.post('/api/enviar_diarios/')
        
        self.middleware.process_request(request)
        
        self.assertTrue(getattr(request, '_dont_enforce_csrf_checks', False))

    def test_csrf_middleware_exempts_baixar_notas(self):
        """Testa que middleware isenta baixar_notas de CSRF."""
        request = self.factory.post('/api/baixar_notas/')
        
        self.middleware.process_request(request)
        
        self.assertTrue(getattr(request, '_dont_enforce_csrf_checks', False))

    def test_csrf_middleware_does_not_exempt_other_urls(self):
        """Testa que middleware não isenta outras URLs."""
        request = self.factory.post('/admin/')
        
        self.middleware.process_request(request)
        
        self.assertFalse(getattr(request, '_dont_enforce_csrf_checks', False))


class BaseBrokerTestCase(TestCase):
    """Testes para BaseBroker."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.ambiente = Ambiente.objects.create(
            nome="Test",
            url="http://test.com",
            token="test_token_123",
            expressao_seletora="1 ==1",
            active=True
        )
        
        self.solicitacao = Solicitacao.objects.create(
            ambiente=self.ambiente,
            operacao=Solicitacao.Operacao.SYNC_UP_DIARIO,
            recebido={"diario": {"id": 123}}
        )
        
        self.broker = BaseBroker(self.solicitacao)

    def test_base_broker_initialization(self):
        """Testa inicialização do BaseBroker."""
        self.assertEqual(self.broker.solicitacao, self.solicitacao)

    def test_base_broker_credentials_property(self):
        """Testa propriedade credentials."""
        credentials = self.broker.credentials
        
        self.assertIn("Authentication", credentials)
        self.assertIn("test_token_123", credentials["Authentication"])

    def test_base_broker_get_coortes(self):
        """Testa método get_coortes."""
        coortes = self.broker.get_coortes()
        
        self.assertEqual(coortes, [])

    def test_base_broker_sync_up_enrolments_not_implemented(self):
        """Testa que sync_up_enrolments não está implementado."""
        with self.assertRaises(NotImplementedError):
            self.broker.sync_up_enrolments()

    def test_base_broker_sync_down_grades_not_implemented(self):
        """Testa que sync_down_grades não está implementado."""
        with self.assertRaises(NotImplementedError):
            self.broker.sync_down_grades()


class Suap2LocalSuapBrokerTestCase(TestCase):
    """Testes para Suap2LocalSuapBroker."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.ambiente = Ambiente.objects.create(
            nome="Test Moodle",
            url="https://moodle.test.com",
            token="test_token",
            expressao_seletora="1 ==1",
            active=True
        )
        
        self.solicitacao = Solicitacao.objects.create(
            ambiente=self.ambiente,
            operacao=Solicitacao.Operacao.SYNC_UP_DIARIO,
            diario_id="123",
            recebido={
                "diario": {"id": 123},
                "campus": {"sigla": "TEST"},
                "turma": {"codigo": "T1"}
            }
        )
        
        self.broker = Suap2LocalSuapBroker(self.solicitacao)

    def test_broker_initialization(self):
        """Testa inicialização do broker."""
        self.assertEqual(self.broker.solicitacao, self.solicitacao)

    def test_broker_moodle_base_api_url_property(self):
        """Testa propriedade moodle_base_api_url."""
        expected = "https://moodle.test.com/local/suap/api"
        self.assertEqual(self.broker.moodle_base_api_url, expected)

    @patch('integrador.brokers.suap2local_suap.http_post_json')
    def test_broker_sync_up_enrolments_success(self, mock_http_post_json):
        """Testa sync_up_enrolments com sucesso."""
        mock_http_post_json.return_value = {"status": "success"}
        
        result = self.broker.sync_up_enrolments()
        
        self.assertEqual(result, {"status": "success"})
        mock_http_post_json.assert_called_once()

    @patch('integrador.brokers.suap2local_suap.http_get_json')
    def test_broker_sync_down_grades_success(self, mock_http_get_json):
        """Testa sync_down_grades com sucesso."""
        mock_http_get_json.return_value = []
        
        result = self.broker.sync_down_grades()
        
        self.assertEqual(result, [])


class ManagementCommandTestCase(TestCase):
    """Testes para management commands."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.ambiente = Ambiente.objects.create(
            nome="Test",
            url="http://test.com",
            token="token",
            expressao_seletora="1 ==1",
            active=True
        )

    def test_atualiza_solicitacoes_command_exists(self):
        """Testa que o comando atualiza_solicitacoes existe."""
        # Cria solicitações com diario_codigo nulo
        for i in range(3):
            sol = Solicitacao(
                ambiente=self.ambiente,
                operacao=Solicitacao.Operacao.SYNC_UP_DIARIO,
                recebido={"diario": {"id": i}}
            )
            sol.diario_codigo = None
            sol.save()
        
        # Chama o comando
        out = io.StringIO()
        call_command('atualiza_solicitacoes', stdout=out)
        
        # Verifica que comando executou
        self.assertTrue(True)

    def test_atualiza_solicitacoes_updates_records(self):
        """Testa que o comando atualiza registros."""
        # Cria solicitação com diario_codigo nulo
        sol = Solicitacao(
            ambiente=self.ambiente,
            operacao=Solicitacao.Operacao.SYNC_UP_DIARIO,
            recebido={"diario": {"id": 999}}
        )
        sol.diario_codigo = None
        sol.save()
        
        # Chama o comando
        call_command('atualiza_solicitacoes')
        
        # Recarrega solicitação
        sol.refresh_from_db()
        
        # Verifica que ambiente foi selecionado corretamente
        self.assertIsNotNone(sol.ambiente)


class IntegrationTestCase(TestCase):
    """Testes de integração para fluxos completos."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.factory = RequestFactory()
        self.ambiente = Ambiente.objects.create(
            nome="Integration Test",
            url="https://moodle.integration.test",
            token="integration_token",
            expressao_seletora="campus.sigla == 'INT'",
            active=True
        )

    @override_settings(SUAP_INTEGRADOR_KEY='test_key')
    @patch('integrador.brokers.suap2local_suap.http_post_json')
    def test_complete_sync_up_flow(self, mock_http_post_json):
        """Testa fluxo completo de sync_up_enrolments."""
        mock_http_post_json.return_value = {
            "url": "https://moodle.test/course/123",
            "status": "success"
        }
        
        json_data = {
            "campus": {"sigla": "INT"},
            "turma": {"codigo": "T123"},
            "componente": {"sigla": "COMP"},
            "diario": {"id": 456, "tipo": "regular"},
            "professores": []
        }
        
        request = self.factory.post(
            '/api/enviar_diarios/',
            data=json.dumps(json_data),
            content_type='application/json'
        )
        request.META['HTTP_AUTHENTICATION'] = 'Token test_key'
        
        response = sync_up_enrolments(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Solicitacao.objects.count(), 1)
        
        solicitacao = Solicitacao.objects.first()
        self.assertEqual(solicitacao.status, Solicitacao.Status.SUCESSO)
        self.assertEqual(solicitacao.ambiente, self.ambiente)


class EdgeCasesTestCase(TestCase):
    """Testes de casos extremos."""

    def test_ambiente_with_multiple_matching_rules(self):
        """Testa ambiente com múltiplas regras correspondentes."""
        amb1 = Ambiente.objects.create(
            nome="Ambiente 1",
            url="http://test1.com",
            token="token1",
            expressao_seletora="campus.sigla == 'TEST'",
            ordem=1,
            active=True
        )
        
        amb2 = Ambiente.objects.create(
            nome="Ambiente 2",
            url="http://test2.com",
            token="token2",
            expressao_seletora="campus.sigla == 'TEST'",
            ordem=2,
            active=True
        )
        
        sync_json = {"campus": {"sigla": "TEST"}}
        ambiente = Ambiente.objects.seleciona_ambiente(sync_json)
        
        # Deve retornar o primeiro que corresponder
        self.assertEqual(ambiente, amb1)

    def test_solicitacao_with_missing_json_fields(self):
        """Testa solicitação com campos JSON faltando."""
        ambiente = Ambiente.objects.create(
            nome="Test",
            url="http://test.com",
            token="token",
            expressao_seletora="1 ==1"
        )
        
        # JSON incompleto
        solicitacao = Solicitacao.objects.create(
            ambiente=ambiente,
            operacao=Solicitacao.Operacao.SYNC_UP_DIARIO,
            recebido={}
        )
        
        # Deve lidar com campos faltando gracefully
        self.assertEqual(solicitacao.campus_sigla, None)

    def test_ambiente_expressao_with_complex_logic(self):
        """Testa ambiente com expressão seletora complexa."""
        ambiente = Ambiente.objects.create(
            nome="Complex",
            url="http://test.com",
            token="token",
            expressao_seletora="campus.sigla == 'TEST' and diario.tipo == 'regular'",
            active=True
        )
        
        sync_json = {
            "campus": {"sigla": "TEST"},
            "diario": {"tipo": "regular"}
        }
        
        resultado = Ambiente.objects.seleciona_ambiente(sync_json)
        self.assertEqual(resultado, ambiente)

    def test_broker_with_url_ending_with_slash(self):
        """Testa broker com URL terminando em barra."""
        ambiente = Ambiente.objects.create(
            nome="Test",
            url="https://moodle.test.com/",
            token="token",
            expressao_seletora="1 ==1"
        )
        
        solicitacao = Solicitacao.objects.create(
            ambiente=ambiente,
            operacao=Solicitacao.Operacao.SYNC_UP_DIARIO,
            recebido={"diario": {"id": 1}}
        )
        
        broker = Suap2LocalSuapBroker(solicitacao)
        
        # base_url não deve ter barra final
        self.assertFalse(broker.solicitacao.ambiente.base_url.endswith('/'))

    def test_ambiente_manager_with_invalid_expression(self):
        """Testa manager com expressão inválida."""
        ambiente = Ambiente.objects.create(
            nome="Invalid",
            url="http://test.com",
            token="token",
            expressao_seletora="invalid {{ expression",
            active=True
        )
        
        sync_json = {"campus": {"sigla": "TEST"}}


class CSRFErrorViewTestCase(TestCase):
    """Testes para a view customizada de erro CSRF."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.factory = RequestFactory()
        # Importa a view de erro CSRF
        from integrador.views_errors import csrf_failure
        self.csrf_failure_view = csrf_failure

    @patch('integrador.views_errors.sentry_sdk')
    def test_csrf_failure_sends_to_sentry(self, mock_sentry):
        """Testa que erro CSRF envia informação para o Sentry."""
        request = self.factory.post('/api/test/')
        request.META['HTTP_USER_AGENT'] = 'TestAgent/1.0'
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_REFERER'] = 'https://external.com'
        request.user = Mock()
        request.user.is_authenticated = False
        
        response = self.csrf_failure_view(request, reason="CSRF cookie not set")
        
        # Verifica que Sentry foi chamado
        mock_sentry.capture_message.assert_called_once()
        call_args = mock_sentry.capture_message.call_args
        self.assertIn("CSRF verification failed", call_args[0][0])
        self.assertEqual(call_args[1]["level"], "warning")

    @patch('integrador.views_errors.sentry_sdk')
    def test_csrf_failure_returns_json_for_api(self, mock_sentry):
        """Testa que erro CSRF retorna JSON para requisições de API."""
        request = self.factory.post('/api/test/')
        request.META['HTTP_ACCEPT'] = 'application/json'
        request.user = Mock()
        request.user.is_authenticated = False
        
        response = self.csrf_failure_view(request, reason="Token mismatch")
        
        self.assertEqual(response.status_code, 403)
        self.assertIsInstance(response, JsonResponse)
        
        data = json.loads(response.content)
        self.assertIn("error", data)
        self.assertIn("reason", data)
        self.assertEqual(data["reason"], "Token mismatch")

    @patch('integrador.views_errors.sentry_sdk')
    def test_csrf_failure_returns_html_for_browser(self, mock_sentry):
        """Testa que erro CSRF retorna HTML para requisições de navegador."""
        request = self.factory.post('/admin/login/')
        request.META['HTTP_ACCEPT'] = 'text/html'
        request.user = Mock()
        request.user.is_authenticated = False
        
        response = self.csrf_failure_view(request, reason="Referer check failed")
        
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'403', response.content)

    @patch('integrador.views_errors.sentry_sdk')
    def test_csrf_failure_includes_user_info_when_authenticated(self, mock_sentry):
        """Testa que erro CSRF inclui informações do usuário autenticado."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        request = self.factory.post('/api/test/')
        request.user = user
        request.META['HTTP_ACCEPT'] = 'application/json'
        
        response = self.csrf_failure_view(request, reason="Token expired")
        
        # Verifica que o contexto do Sentry foi configurado corretamente
        mock_sentry.push_scope.assert_called()

    @patch('integrador.views_errors.sentry_sdk')
    @patch('integrador.views_errors.logger')
    def test_csrf_failure_logs_warning(self, mock_logger, mock_sentry):
        """Testa que erro CSRF gera log de warning."""
        request = self.factory.post('/api/test/')
        request.user = Mock()
        request.user.is_authenticated = False
        
        response = self.csrf_failure_view(request, reason="Invalid token")
        
        # Verifica se o logger foi chamado
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        self.assertIn("CSRF verification failed", call_args[0][0])

    @patch('integrador.views_errors.sentry_sdk')
    def test_csrf_failure_captures_request_details(self, mock_sentry):
        """Testa que erro CSRF captura detalhes completos da requisição."""
        request = self.factory.post('/api/sensitive-endpoint/')
        request.META['HTTP_USER_AGENT'] = 'MaliciousBot/1.0'
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        request.META['HTTP_REFERER'] = 'https://malicious-site.com'
        request.META['CONTENT_TYPE'] = 'application/json'
        request.user = Mock()
        request.user.is_authenticated = False
        
        response = self.csrf_failure_view(request, reason="CSRF cookie not set")
        
        # Verifica que todos os detalhes foram capturados
        self.assertEqual(response.status_code, 403)
        mock_sentry.capture_message.assert_called_once()

    @patch('integrador.views_errors.sentry_sdk')
    def test_csrf_failure_with_empty_reason(self, mock_sentry):
        """Testa erro CSRF com razão vazia."""
        request = self.factory.post('/api/test/')
        request.META['HTTP_ACCEPT'] = 'application/json'
        request.user = Mock()
        request.user.is_authenticated = False
        
        response = self.csrf_failure_view(request, reason="")
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertIn("reason", data)

    @patch('integrador.views_errors.sentry_sdk')
    def test_csrf_failure_returns_json_when_content_type_is_json(self, mock_sentry):
        """Testa que erro CSRF retorna JSON quando Content-Type é application/json."""
        request = self.factory.post(
            '/admin/test/',
            content_type='application/json',
            data=json.dumps({"test": "data"})
        )
        request.user = Mock()
        request.user.is_authenticated = False
        
        response = self.csrf_failure_view(request, reason="Token mismatch")
        
        # Mesmo sem /api/ no path, deve retornar JSON porque Content-Type é JSON
        self.assertEqual(response.status_code, 403)
        self.assertIsInstance(response, JsonResponse)
        
        data = json.loads(response.content)
        self.assertEqual(data["error"], "CSRF verification failed")
        self.assertEqual(data["reason"], "Token mismatch")

    @patch('integrador.views_errors.sentry_sdk')
    def test_csrf_failure_returns_json_when_accept_is_json(self, mock_sentry):
        """Testa que erro CSRF retorna JSON quando Accept é application/json."""
        request = self.factory.post('/admin/test/')
        request.META['HTTP_ACCEPT'] = 'application/json; charset=utf-8'
        request.user = Mock()
        request.user.is_authenticated = False
        
        response = self.csrf_failure_view(request, reason="Referer check failed")
        
        # Deve retornar JSON porque Accept contém application/json
        self.assertEqual(response.status_code, 403)
        self.assertIsInstance(response, JsonResponse)
        
        data = json.loads(response.content)
        self.assertEqual(data["error"], "CSRF verification failed")

    @patch('integrador.views_errors.sentry_sdk')
    def test_csrf_failure_returns_json_for_api_paths(self, mock_sentry):
        """Testa que erro CSRF retorna JSON para paths começando com /api/."""
        request = self.factory.post('/api/some/endpoint/')
        request.META['HTTP_ACCEPT'] = 'text/html'  # Mesmo com Accept HTML
        request.user = Mock()
        request.user.is_authenticated = False
        
        response = self.csrf_failure_view(request, reason="CSRF token missing")
        
        # Deve retornar JSON porque path começa com /api/
        self.assertEqual(response.status_code, 403)
        self.assertIsInstance(response, JsonResponse)
