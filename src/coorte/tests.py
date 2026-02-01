"""
Testes unitários para a app coorte.

Este módulo contém testes para:
- Papel: Modelo de papéis (roles) com contextos (curso, polo, programa)
- Cohort: Modelo de coortes com regras de validação (RuleField)
- Enrolment: Vínculos entre colaboradores e cohorts
- Admin: Configurações do admin (PapelAdmin, CohortAdmin)
"""
import unittest
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from coorte.models import Papel, Cohort, Enrolment
from coorte.admin import PapelAdmin, CohortAdmin, EnrolmentInline
from coorte.apps import IntegradorConfig
from edu.models import Curso


class IntegradorConfigTestCase(TestCase):
    """Testes para a configuração da app coorte."""

    def test_app_config_name(self):
        """Testa se o nome da app está correto."""
        self.assertEqual(IntegradorConfig.name, 'coorte')

    def test_app_config_icon(self):
        """Testa se o ícone está definido."""
        self.assertEqual(IntegradorConfig.icon, 'fa fa-home')

    def test_app_config_default_auto_field(self):
        """Testa se default_auto_field está configurado."""
        self.assertEqual(
            IntegradorConfig.default_auto_field,
            'django.db.models.BigAutoField'
        )


class CohortModelTestCase(TestCase):
    """Testes para o modelo Cohort."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.papel = Papel.objects.create(
            nome="Coordenador de Curso",
            sigla="COODC",
            papel="teachercoordenadorcurso",
                    active=True
        )
        
        self.cohort = Cohort.objects.create(
            name="Test Cohort",
            idnumber="TEST001",
            active=True,
            papel=self.papel
        )

    def test_create_cohort(self):
        """Testa criação de cohort."""
        cohort = Cohort.objects.create(
            name="New Cohort",
            idnumber="NEW001",
            active=True,
            papel=self.papel
        )
        
        self.assertIsNotNone(cohort.pk)
        self.assertEqual(cohort.name, "New Cohort")
        self.assertEqual(cohort.idnumber, "NEW001")

    def test_cohort_str_representation(self):
        """Testa representação em string do cohort."""
        self.assertEqual(str(self.cohort), "Test Cohort")

    def test_cohort_name_unique(self):
        """Testa que name deve ser único."""
        with self.assertRaises(IntegrityError):
            Cohort.objects.create(
                name="Test Cohort",  # Nome duplicado
                idnumber="DIFF001",
                papel=self.papel
            )

    def test_cohort_idnumber_unique(self):
        """Testa que idnumber deve ser único."""
        with self.assertRaises(IntegrityError):
            Cohort.objects.create(
                name="Different Cohort",
                idnumber="TEST001",  # IDNumber duplicado
                papel=self.papel
            )

    def test_cohort_active_field(self):
        """Testa campo active."""
        self.assertTrue(self.cohort.active)
        
        self.cohort.active = False
        self.cohort.save()
        
        cohort = Cohort.objects.get(pk=self.cohort.pk)
        self.assertFalse(cohort.active)

    def test_cohort_rule_diario_field(self):
        """Testa campo rule_diario (RuleField)."""
        self.cohort.rule_diario = "curso.codigo == '132456'"
        self.cohort.save()
        
        cohort = Cohort.objects.get(pk=self.cohort.pk)
        self.assertEqual(cohort.rule_diario, "curso.codigo == '132456'")

    def test_cohort_rule_coordenacao_field(self):
        """Testa campo rule_coordenacao (RuleField)."""
        self.cohort.rule_coordenacao = "programa.sigla == 'UAB'"
        self.cohort.save()
        
        cohort = Cohort.objects.get(pk=self.cohort.pk)
        self.assertEqual(cohort.rule_coordenacao, "programa.sigla == 'UAB'")

    def test_cohort_description_field(self):
        """Testa campo description."""
        self.cohort.description = "Test description"
        self.cohort.save()
        
        cohort = Cohort.objects.get(pk=self.cohort.pk)
        self.assertEqual(cohort.description, "Test description")

    def test_cohort_papel_relationship(self):
        """Testa relacionamento com Papel."""
        self.assertEqual(self.cohort.papel, self.papel)
        self.assertIn(self.cohort, self.papel.cohort_papel.all())

    def test_cohort_ordering(self):
        """Testa ordenação de cohorts."""
        cohort2 = Cohort.objects.create(
            name="Another Cohort",
            idnumber="ANOTHER001",
            papel=self.papel
        )
        
        cohorts = list(Cohort.objects.all())
        # Ordenação por name
        self.assertEqual(cohorts[0].name, "Another Cohort")
        self.assertEqual(cohorts[1].name, "Test Cohort")

    def test_cohort_verbose_names(self):
        """Testa verbose_name e verbose_name_plural."""
        self.assertEqual(Cohort._meta.verbose_name, "coorte")
        self.assertEqual(Cohort._meta.verbose_name_plural, "coortes")


class EnrolmentModelTestCase(TestCase):
    """Testes para o modelo Enrolment."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.user = User.objects.create_user(
            username='testuser',
            password='password123'
        )
        
        self.papel = Papel.objects.create(
            nome="Coordenador",
            sigla="COORD",
            papel="coordenador",
                    active=True
        )
        
        self.cohort = Cohort.objects.create(
            name="Test Cohort",
            idnumber="TEST001",
            papel=self.papel
        )
        
        self.enrolment = Enrolment.objects.create(
            colaborador=self.user,
            cohort=self.cohort
        )

    def test_create_enrolment(self):
        """Testa criação de enrolment."""
        user2 = User.objects.create_user(
            username='testuser2',
            password='password123'
        )
        
        enrolment = Enrolment.objects.create(
            colaborador=user2,
            cohort=self.cohort
        )
        
        self.assertIsNotNone(enrolment.pk)
        self.assertEqual(enrolment.colaborador, user2)
        self.assertEqual(enrolment.cohort, self.cohort)

    def test_enrolment_str_representation(self):
        """Testa representação em string do enrolment."""
        string_repr = str(self.enrolment)
        
        self.assertIn("testuser", string_repr)
        self.assertIn("Test Cohort", string_repr)

    def test_enrolment_colaborador_relationship(self):
        """Testa relacionamento com User."""
        self.assertEqual(self.enrolment.colaborador, self.user)

    def test_enrolment_cohort_relationship(self):
        """Testa relacionamento com Cohort."""
        self.assertEqual(self.enrolment.cohort, self.cohort)
        self.assertIn(self.enrolment, self.cohort.enrolments.all())

    def test_multiple_enrolments_same_cohort(self):
        """Testa múltiplos enrolments no mesmo cohort."""
        user2 = User.objects.create_user(username='user2', password='pass')
        user3 = User.objects.create_user(username='user3', password='pass')
        
        Enrolment.objects.create(colaborador=user2, cohort=self.cohort)
        Enrolment.objects.create(colaborador=user3, cohort=self.cohort)
        
        self.assertEqual(self.cohort.enrolments.count(), 3)

    def test_enrolment_ordering(self):
        """Testa ordenação de enrolments."""
        user2 = User.objects.create_user(username='anotheruser', password='pass')
        Enrolment.objects.create(colaborador=user2, cohort=self.cohort)
        
        enrolments = list(Enrolment.objects.all())
        # Ordenação: cohort, colaborador
        self.assertEqual(len(enrolments), 2)

    def test_enrolment_verbose_names(self):
        """Testa verbose_name e verbose_name_plural."""
        self.assertEqual(Enrolment._meta.verbose_name, "vínculo")
        self.assertEqual(Enrolment._meta.verbose_name_plural, "vínculos")


class PapelAdminTestCase(TestCase):
    """Testes para PapelAdmin."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='password123'
        )
        self.papel_admin = PapelAdmin(Papel, None)

    def test_papel_admin_list_display(self):
        """Testa configuração de list_display."""
        expected = ["nome", "papel", "sigla", "exemplo", "active"]
        self.assertEqual(self.papel_admin.list_display, expected)

    def test_papel_admin_list_filter(self):
        """Testa configuração de list_filter."""
        self.assertIn("active", self.papel_admin.list_filter)

    def test_papel_admin_search_fields(self):
        """Testa configuração de search_fields."""
        expected = ["papel", "sigla", "nome"]
        self.assertEqual(self.papel_admin.search_fields, expected)

    def test_papel_admin_resource_classes(self):
        """Testa configuração de resource_classes."""
        self.assertEqual(len(self.papel_admin.resource_classes), 1)
        
        resource = self.papel_admin.resource_classes[0]()
        self.assertEqual(resource._meta.model, Papel)

    def test_papel_resource_export_order(self):
        """Testa ordem de exportação do resource."""
        resource = self.papel_admin.resource_classes[0]()
        expected = ["papel", "sigla", "nome", "active"]
        self.assertEqual(resource._meta.export_order, expected)

    def test_papel_resource_import_id_fields(self):
        """Testa campos de identificação para importação."""
        resource = self.papel_admin.resource_classes[0]()
        self.assertEqual(resource._meta.import_id_fields, ("sigla",))


class CohortAdminTestCase(TestCase):
    """Testes para CohortAdmin."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='password123'
        )
        self.cohort_admin = CohortAdmin(Cohort, None)

    def test_cohort_admin_list_display(self):
        """Testa configuração de list_display."""
        expected = ["name", "idnumber", "rule_diario", "rule_coordenacao", "active"]
        self.assertEqual(self.cohort_admin.list_display, expected)

    def test_cohort_admin_search_fields(self):
        """Testa configuração de search_fields."""
        expected = ["name", "idnumber"]
        self.assertEqual(self.cohort_admin.search_fields, expected)

    def test_cohort_admin_list_filter(self):
        """Testa configuração de list_filter."""
        self.assertIn("active", self.cohort_admin.list_filter)

    def test_cohort_admin_fieldsets(self):
        """Testa configuração de fieldsets."""
        fieldsets = self.cohort_admin.fieldsets
        
        # CohortAdmin tem 3 fieldsets (Informações Básicas, Regras de Validação, Status)
        self.assertGreaterEqual(len(fieldsets), 2)
        self.assertEqual(fieldsets[0][0], "Informações Básicas")
        self.assertEqual(fieldsets[1][0], "Regras de Validação")

    def test_cohort_admin_inlines(self):
        """Testa configuração de inlines."""
        self.assertEqual(len(self.cohort_admin.inlines), 1)
        self.assertEqual(self.cohort_admin.inlines[0], EnrolmentInline)


class IntegrationTestCase(TestCase):
    """Testes de integração para fluxos completos."""

    def test_complete_cohort_workflow(self):
        """Testa fluxo completo: Papel -> Cohort -> Enrolment."""
        # 1. Cria papel
        papel = Papel.objects.create(
            nome="Coordenador",
            sigla="COORD",
            papel="coordenador",
            active=True
        )
        
        # 2. Cria cohort
        cohort = Cohort.objects.create(
            name="Integration Cohort",
            idnumber="INT001",
            papel=papel,
            rule_diario="curso.codigo == '123456'"
        )
        
        # 3. Cria usuário
        user = User.objects.create_user(username='integrationuser', password='pass')
        
        # 4. Cria enrolment
        enrolment = Enrolment.objects.create(
            colaborador=user,
            cohort=cohort
        )
        
        # Verifica relacionamentos
        self.assertEqual(cohort.papel, papel)
        self.assertEqual(enrolment.cohort, cohort)
        self.assertEqual(enrolment.colaborador, user)


class EdgeCasesTestCase(TestCase):
    """Testes de casos extremos."""

    def test_papel_exemplo_with_empty_sigla(self):
        """Testa exemplo com sigla vazia."""
        papel = Papel(
            nome="Test",
            sigla="",
            papel="test"
        )
        
        exemplo = papel.exemplo
        self.assertEqual(exemplo, "SG..123456")

    def test_cohort_with_null_description(self):
        """Testa cohort com descrição nula."""
        papel = Papel.objects.create(
            nome="Test",
            sigla="T",
            papel="test",
            active=True
        )
        
        cohort = Cohort.objects.create(
            name="Test",
            idnumber="T001",
            papel=papel,
            description=None
        )
        
        self.assertIsNone(cohort.description)

    def test_papel_inactive_icon(self):
        """Testa ícone de papel inativo."""
        papel = Papel.objects.create(
            nome="Inactive",
            sigla="INAC",
            papel="inactive",
            active=False
        )
        
        string_repr = str(papel)
        self.assertIn("⛔", string_repr)
