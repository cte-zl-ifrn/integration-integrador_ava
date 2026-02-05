"""
Testes unitários para a app cohort.

Este módulo contém testes para:
- Role: Modelo de roles
- Cohort: Modelo de cohorts com regras de validação (RuleField)
- Enrolment: Vínculos entre users e cohorts
- Admin: Configurações do admin (RoleAdmin, CohortAdmin)
"""
import unittest
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from cohort.models import Role, Cohort, Enrolment
from cohort.admin import RoleAdmin, CohortAdmin, EnrolmentInline
from cohort.apps import CohortConfig


class IntegradorConfigTestCase(TestCase):
    """Testes para a configuração da app cohort."""

    def test_app_config_name(self):
        """Testa se o name da app está correto."""
        self.assertEqual(CohortConfig.name, 'cohort')

    def test_app_config_icon(self):
        """Testa se o ícone está definido."""
        self.assertEqual(CohortConfig.icon, 'fa fa-home')

    def test_app_config_default_auto_field(self):
        """Testa se default_auto_field está configurado."""
        self.assertEqual(
            CohortConfig.default_auto_field,
            'django.db.models.BigAutoField'
        )


class CohortModelTestCase(TestCase):
    """Testes para o modelo Cohort."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.role = Role.objects.create(
            name="Coordenador de Curso",
            shortname="teachercoordenadorcurso",
            active=True
        )
        
        self.cohort = Cohort.objects.create(
            name="Test Cohort",
            idnumber="TEST001",
            active=True,
            role=self.role
        )

    def test_create_cohort(self):
        """Testa criação de cohort."""
        cohort = Cohort.objects.create(
            name="New Cohort",
            idnumber="NEW001",
            active=True,
            role=self.role
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
                name="Test Cohort",  # Name duplicado
                idnumber="DIFF001",
                role=self.role
            )

    def test_cohort_idnumber_unique(self):
        """Testa que idnumber deve ser único."""
        with self.assertRaises(IntegrityError):
            Cohort.objects.create(
                name="Different Cohort",
                idnumber="TEST001",  # IDNumber duplicado
                role=self.role
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

    def test_cohort_role_relationship(self):
        """Testa relacionamento com Role."""
        self.assertEqual(self.cohort.role, self.role)
        self.assertIn(self.cohort, self.role.cohort_roles.all())

    def test_cohort_ordering(self):
        """Testa ordenação de cohorts."""
        cohort2 = Cohort.objects.create(
            name="Another Cohort",
            idnumber="ANOTHER001",
            role=self.role
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
        
        self.role = Role.objects.create(
            name="Coordenador",
            shortname="COORD",
            active=True
        )
        
        self.cohort = Cohort.objects.create(
            name="Test Cohort",
            idnumber="TEST001",
            role=self.role
        )
        
        self.enrolment = Enrolment.objects.create(
            user=self.user,
            cohort=self.cohort
        )

    def test_create_enrolment(self):
        """Testa criação de enrolment."""
        user2 = User.objects.create_user(
            username='testuser2',
            password='password123'
        )
        
        enrolment = Enrolment.objects.create(
            user=user2,
            cohort=self.cohort
        )
        
        self.assertIsNotNone(enrolment.pk)
        self.assertEqual(enrolment.user, user2)
        self.assertEqual(enrolment.cohort, self.cohort)

    def test_enrolment_str_representation(self):
        """Testa representação em string do enrolment."""
        string_repr = str(self.enrolment)
        
        self.assertIn("testuser", string_repr)
        self.assertIn("Test Cohort", string_repr)

    def test_enrolment_user_relationship(self):
        """Testa relacionamento com User."""
        self.assertEqual(self.enrolment.user, self.user)

    def test_enrolment_cohort_relationship(self):
        """Testa relacionamento com Cohort."""
        self.assertEqual(self.enrolment.cohort, self.cohort)
        self.assertIn(self.enrolment, self.cohort.enrolments.all())

    def test_multiple_enrolments_same_cohort(self):
        """Testa múltiplos enrolments no mesmo cohort."""
        user2 = User.objects.create_user(username='user2', password='pass')
        user3 = User.objects.create_user(username='user3', password='pass')
        
        Enrolment.objects.create(user=user2, cohort=self.cohort)
        Enrolment.objects.create(user=user3, cohort=self.cohort)
        
        self.assertEqual(self.cohort.enrolments.count(), 3)

    def test_enrolment_ordering(self):
        """Testa ordenação de enrolments."""
        user2 = User.objects.create_user(username='anotheruser', password='pass')
        Enrolment.objects.create(user=user2, cohort=self.cohort)
        
        enrolments = list(Enrolment.objects.all())
        # Ordenação: cohort, user
        self.assertEqual(len(enrolments), 2)

    def test_enrolment_verbose_names(self):
        """Testa verbose_name e verbose_name_plural."""
        self.assertEqual(Enrolment._meta.verbose_name, "vínculo")
        self.assertEqual(Enrolment._meta.verbose_name_plural, "vínculos")


class RoleAdminTestCase(TestCase):
    """Testes para RoleAdmin."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='password123'
        )
        self.role_admin = RoleAdmin(Role, None)

    def test_role_admin_list_display(self):
        """Testa configuração de list_display."""
        expected = ["name", "shortname", "active"]
        self.assertEqual(self.role_admin.list_display, expected)

    def test_role_admin_list_filter(self):
        """Testa configuração de list_filter."""
        self.assertIn("active", self.role_admin.list_filter)

    def test_role_admin_search_fields(self):
        """Testa configuração de search_fields."""
        expected = ["name", "shortname"]
        self.assertEqual(self.role_admin.search_fields, expected)

    def test_role_admin_resource_classes(self):
        """Testa configuração de resource_classes."""
        self.assertEqual(len(self.role_admin.resource_classes), 1)
        
        resource = self.role_admin.resource_classes[0]()
        self.assertEqual(resource._meta.model, Role)

    def test_role_resource_export_order(self):
        """Testa ordem de exportação do resource."""
        resource = self.role_admin.resource_classes[0]()
        expected = ["name", "shortname", "active"]
        self.assertEqual(resource._meta.export_order, expected)

    def test_role_resource_import_id_fields(self):
        """Testa campos de identificação para importação."""
        resource = self.role_admin.resource_classes[0]()
        self.assertEqual(resource._meta.import_id_fields, ("shortname",))


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
        """Testa fluxo completo: Role -> Cohort -> Enrolment."""
        # 1. Cria role
        role = Role.objects.create(
            name="Coordenador",
            shortname="COORD",
            active=True
        )
        
        # 2. Cria cohort
        cohort = Cohort.objects.create(
            name="Integration Cohort",
            idnumber="INT001",
            role=role,
            rule_diario="curso.codigo == '123456'"
        )
        
        # 3. Cria usuário
        user = User.objects.create_user(username='integrationuser', password='pass')
        
        # 4. Cria enrolment
        enrolment = Enrolment.objects.create(
            user=user,
            cohort=cohort
        )
        
        # Verifica relacionamentos
        self.assertEqual(cohort.role, role)
        self.assertEqual(enrolment.cohort, cohort)
        self.assertEqual(enrolment.user, user)


class EdgeCasesTestCase(TestCase):
    """Testes de casos extremos."""

    def test_cohort_with_null_description(self):
        """Testa cohort com descrição nula."""
        role = Role.objects.create(
            name="Test",
            shortname="T",
            active=True
        )
        
        cohort = Cohort.objects.create(
            name="Test",
            idnumber="T001",
            role=role,
            description=None
        )
        
        self.assertIsNone(cohort.description)

    def test_role_inactive_icon(self):
        """Testa ícone de role inativo."""
        role = Role.objects.create(
            name="Inactive",
            shortname="INAC",
            active=False
        )
        
        string_repr = str(role)
        self.assertIn("⛔", string_repr)
