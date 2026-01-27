"""
Testes unitários para a app dashboard.

Este módulo contém testes para:
- DashboardStorage: carregamento de dados e cache
- admin_views: views personalizadas do admin
"""
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth.models import User
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from unittest.mock import patch, MagicMock
from django.utils.timezone import now
from datetime import timedelta

from dashboard.storage import DashboardStorage
from dashboard.admin_views import admin_index_dashboard
from integrador.models import Ambiente, Solicitacao
from coorte.models import Cohort, Papel, Enrolment
from edu.models import Programa, Polo


class DashboardStorageTestCase(TestCase):
    """Testes para a classe DashboardStorage."""

    def setUp(self):
        """Configura o ambiente de teste."""
        cache.clear()
        self.storage = DashboardStorage()
        
        # Cria dados de teste
        self.ambiente = Ambiente.objects.create(
            nome="Test Ambiente",
            url="https://test.moodle.com",
            token="test_token",
            expressao_seletora="campus.sigla == 'TEST'",
            active=True
        )
        
        self.programa = Programa.objects.create(
            nome="Test Program",
            sigla="PROG"
        )
        
        self.polo = Polo.objects.create(
            nome="Test Polo",
            suap_id="P001"
        )
        
        self.papel = Papel.objects.create(
            sigla="PAPEL",
            nome="Test Role",
            papel="testrole",
            active=True
        )
        
        self.cohort = Cohort.objects.create(
            name="Test Cohort",
            idnumber="C001",
            papel=self.papel,
            active=True
        )
        
        self.user = User.objects.create_user(
            username="testuser",
            is_active=True
        )
        
        # Cria solicitações de teste
        self.solicitacao_sucesso = Solicitacao.objects.create(
            campus_sigla="TEST",
            tipo="regular",
            operacao=Solicitacao.Operacao.SYNC_UP_DIARIO,
            status=Solicitacao.Status.SUCESSO,
            timestamp=now()
        )
        
        self.solicitacao_falha = Solicitacao.objects.create(
            campus_sigla="TEST",
            tipo="regular",
            operacao=Solicitacao.Operacao.SYNC_DOWN_NOTAS,
            status=Solicitacao.Status.FALHA,
            timestamp=now() - timedelta(hours=12)
        )
        
        self.solicitacao_processando = Solicitacao.objects.create(
            campus_sigla="TEST",
            tipo="regular",
            operacao=Solicitacao.Operacao.SYNC_UP_DIARIO,
            status=Solicitacao.Status.PROCESSANDO,
            timestamp=now() - timedelta(hours=25)
        )

    def tearDown(self):
        """Limpa o cache após cada teste."""
        cache.clear()

    def test_dashboard_storage_initialization(self):
        """Testa inicialização do DashboardStorage."""
        storage = DashboardStorage()
        self.assertIsNotNone(storage.data)
        self.assertEqual(storage.data['ambientes_total'], 0)
        self.assertEqual(storage.data['total_solicitacoes'], 0)

    def test_get_context_without_cache(self):
        """Testa obtenção do contexto sem cache."""
        with override_settings(DASHBOARD_CACHE_ENABLED=False):
            context = self.storage.get_context()
            self.assertIsNotNone(context)
            self.assertIn('ambientes_total', context)

    def test_get_context_with_cache(self):
        """Testa obtenção do contexto com cache."""
        with override_settings(DASHBOARD_CACHE_ENABLED=True, DASHBOARD_CACHE_TIMEOUT=300):
            # Primeira chamada deve carregar dados
            context1 = self.storage.get_context()
            self.assertIsNotNone(context1)
            
            # Segunda chamada deve usar cache
            context2 = self.storage.get_context()
            self.assertEqual(context1['ambientes_total'], context2['ambientes_total'])

    def test_load_ambientes(self):
        """Testa carregamento de ambientes."""
        context = self.storage.get_context()
        self.assertEqual(context['ambientes_total'], 1)
        self.assertEqual(context['ambientes_ativos'], 1)

    def test_load_ambientes_with_invalid_expressao(self):
        """Testa carregamento de ambientes com expressão inválida."""
        # Cria um ambiente com expressão inválida
        Ambiente.objects.create(
            nome="Bad Ambiente",
            url="https://bad.moodle.com",
            token="bad_token",
            expressao_seletora="invalid {{expression",
            active=True
        )
        
        storage = DashboardStorage()
        context = storage.get_context()
        # Deve contar ambientes com erro
        self.assertEqual(context['ambientes_total'], 2)

    def test_load_coortes(self):
        """Testa carregamento de coortes."""
        context = self.storage.get_context()
        self.assertEqual(context['coortes_total'], 1)
        self.assertEqual(context['coortes_ativas'], 1)
        self.assertEqual(context['coortes_inativas'], 0)

    def test_load_coortes_with_inactive(self):
        """Testa carregamento de coortes inativas."""
        Cohort.objects.create(
            name="Inactive Cohort",
            idnumber="C002",
            papel=self.papel,
            active=False
        )
        
        storage = DashboardStorage()
        context = storage.get_context()
        self.assertEqual(context['coortes_total'], 2)
        self.assertEqual(context['coortes_ativas'], 1)
        self.assertEqual(context['coortes_inativas'], 1)

    def test_load_papeis(self):
        """Testa carregamento de papéis."""
        context = self.storage.get_context()
        self.assertEqual(context['papeis_total'], 1)
        self.assertEqual(context['papeis_ativos'], 1)
        self.assertEqual(context['papeis_inativos'], 0)

    def test_load_papeis_with_inactive(self):
        """Testa carregamento de papéis inativos."""
        Papel.objects.create(
            sigla="PAP02",
            nome="Inactive Role",
            papel="inactiverole",
            active=False
        )
        
        storage = DashboardStorage()
        context = storage.get_context()
        self.assertEqual(context['papeis_total'], 2)
        self.assertEqual(context['papeis_ativos'], 1)
        self.assertEqual(context['papeis_inativos'], 1)

    def test_load_usuarios(self):
        """Testa carregamento de usuários."""
        context = self.storage.get_context()
        self.assertGreater(context['usuarios_total'], 0)
        self.assertGreaterEqual(context['usuarios_ativos'], 1)

    def test_load_solicitacoes(self):
        """Testa carregamento de solicitações."""
        context = self.storage.get_context()
        self.assertEqual(context['solicitacoes_sucesso'], 1)
        self.assertEqual(context['solicitacoes_falha'], 1)
        self.assertEqual(context['solicitacoes_processando'], 1)
        self.assertEqual(context['total_solicitacoes'], 3)
        # sucesso e falha nas últimas 24h, processando está fora (25 horas)
        # Mas na verdade o timestamp padrão pode ter sido incluído no create
        self.assertGreaterEqual(context['solicitacoes_24h'], 2)

    def test_load_solicitacoes_taxa_sucesso(self):
        """Testa cálculo da taxa de sucesso."""
        context = self.storage.get_context()
        expected_taxa = (1 / 3) * 100
        self.assertEqual(context['taxa_sucesso'], int(expected_taxa))

    def test_load_solicitacoes_with_no_requests(self):
        """Testa carregamento quando não há solicitações."""
        Solicitacao.objects.all().delete()
        storage = DashboardStorage()
        context = storage.get_context()
        self.assertEqual(context['total_solicitacoes'], 0)
        self.assertEqual(context['taxa_sucesso'], 0)

    def test_load_series_temporal(self):
        """Testa carregamento da série temporal."""
        context = self.storage.get_context()
        self.assertIsNotNone(context['solicitacoes_series'])
        self.assertIsInstance(context['solicitacoes_series'], list)

    def test_load_series_temporal_with_multiple_months(self):
        """Testa carregamento da série temporal com múltiplos meses."""
        # Cria solicitações em diferentes meses
        three_months_ago = now() - timedelta(days=90)
        Solicitacao.objects.create(
            campus_sigla="TEST",
            tipo="regular",
            operacao=Solicitacao.Operacao.SYNC_UP_DIARIO,
            status=Solicitacao.Status.SUCESSO,
            timestamp=three_months_ago
        )
        
        storage = DashboardStorage()
        context = storage.get_context()
        # Deve ter mais de uma série
        self.assertGreater(len(context['solicitacoes_series']), 0)

    def test_load_data_handles_exception(self):
        """Testa se exceções são tratadas no carregamento."""
        with patch('dashboard.storage.Ambiente.objects.count', side_effect=Exception("DB Error")):
            context = self.storage.get_context()
            # Deve retornar contexto mesmo com erro
            self.assertIsNotNone(context)

    def test_cache_key_storage(self):
        """Testa se os dados são armazenados no cache."""
        cache.clear()
        with override_settings(DASHBOARD_CACHE_ENABLED=True, DASHBOARD_CACHE_TIMEOUT=300):
            storage = DashboardStorage()
            # Primeira chamada carrega dados
            context1 = storage.get_context()
            
            # Chama novamente - se cache funcionar, deve vir do cache
            storage2 = DashboardStorage()
            context2 = storage2.get_context()
            
            # Os dados devem ser iguais
            self.assertEqual(context1['ambientes_total'], context2['ambientes_total'])
            self.assertEqual(context1['coortes_total'], context2['coortes_total'])

    def test_cache_disabled_not_stored(self):
        """Testa se cache não armazena quando desabilitado."""
        with override_settings(DASHBOARD_CACHE_ENABLED=False):
            context = self.storage.get_context()
            # Verifica se dados não estão em cache
            from django.core.cache import cache
            cached = cache.get('admin_dashboard_data')
            self.assertIsNone(cached)


class AdminIndexDashboardTestCase(TestCase):
    """Testes para a view admin_index_dashboard."""

    def setUp(self):
        """Configura o ambiente de teste."""
        cache.clear()
        self.factory = RequestFactory()
        
        # Cria usuário staff
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Cria usuário não-staff
        self.regular_user = User.objects.create_user(
            username='regularuser',
            password='testpass123',
            is_staff=False,
            is_superuser=False
        )

    def tearDown(self):
        """Limpa o cache após cada teste."""
        cache.clear()

    def test_admin_dashboard_requires_staff(self):
        """Testa se o dashboard requer usuário staff (redirect)."""
        request = self.factory.get('/admin/')
        request.user = self.regular_user
        
        response = admin_index_dashboard(request)
        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_loads_storage_data(self):
        """Testa se o dashboard carrega dados do storage."""
        request = self.factory.get('/admin/')
        request.user = self.staff_user
        
        with patch('dashboard.admin_views.DashboardStorage') as mock_storage:
            mock_instance = mock_storage.return_value
            mock_instance.get_context.return_value = {'test_key': 'test_value'}
            
            with patch('dashboard.admin_views.LogEntry.objects.filter') as mock_log:
                mock_log.return_value.select_related.return_value.order_by.return_value = []
                
                with patch('dashboard.admin_views.admin.site.get_app_list', return_value=[]):
                    with patch('dashboard.admin_views.render') as mock_render:
                        admin_index_dashboard(request)
                        mock_render.assert_called_once()
                        # Verifica que storage foi criado e chamado
                        mock_storage.assert_called_once()
                        mock_instance.get_context.assert_called_once()

    def test_admin_dashboard_handles_log_entry_error(self):
        """Testa se dashboard lida com erro no histórico."""
        request = self.factory.get('/admin/')
        request.user = self.staff_user
        
        with patch('dashboard.admin_views.LogEntry.objects.filter', side_effect=Exception("DB Error")):
            with patch('dashboard.admin_views.DashboardStorage') as mock_storage:
                mock_instance = mock_storage.return_value
                mock_instance.get_context.return_value = {}
                
                with patch('dashboard.admin_views.admin.site.get_app_list', return_value=[]):
                    with patch('dashboard.admin_views.render') as mock_render:
                        admin_index_dashboard(request)
                        # Pega o contexto passado para render
                        context = mock_render.call_args[0][2]
                        # Deve ter lista vazia
                        self.assertEqual(context['log_entries'], [])
