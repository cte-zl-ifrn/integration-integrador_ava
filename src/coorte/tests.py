"""
Testes unitários para a app coorte.

Este módulo contém testes para:
- Papel: Modelo de papéis (roles) com contextos (curso, polo, programa)
- Cohort: Modelo de coortes com regras de validação (RuleField)
- Enrolment: Vínculos entre colaboradores e cohorts
- Coorte (polymorphic): Modelos polimórficos CoorteCurso, CoortePolo, CoortePrograma
- Vinculo: Vínculos com coortes polimórficas
- Admin: Configurações do admin (PapelAdmin, CohortAdmin)
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from unittest.mock import patch, Mock, MagicMock

from coorte.models import (
    Papel, Cohort, Enrolment,
    Coorte, CoorteCurso, CoortePolo, CoortePrograma, Vinculo
)
from coorte.admin import PapelAdmin, CohortAdmin, EnrolmentInline, PapelFilter
from coorte.apps import IntegradorConfig
from edu.models import Curso, Polo, Programa


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


class PapelModelTestCase(TestCase):
    """Testes para o modelo Papel."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.papel_curso = Papel.objects.create(
            contexto=Papel.Contexto.CURSO,
            nome="Coordenador de Curso",
            sigla="COODC",
            papel="teachercoordenadorcurso",
                    active=True
        )

    def test_create_papel(self):
        """Testa criação de papel."""
        papel = Papel.objects.create(
            contexto=Papel.Contexto.POLO,
            nome="Coordenador de Pólo",
            sigla="COODP",
            papel="coordenadordepolo",
                    active=True
        )
        
        self.assertIsNotNone(papel.pk)
        self.assertEqual(papel.nome, "Coordenador de Pólo")
        self.assertEqual(papel.contexto, Papel.Contexto.POLO)

    def test_papel_str_representation(self):
        """Testa representação em string do papel."""
        string_repr = str(self.papel_curso)
        
        self.assertIn("Coordenador de Curso", string_repr)
        self.assertIn("✅", string_repr)  # active icon

    def test_papel_exemplo_property(self):
        """Testa propriedade exemplo."""
        exemplo = self.papel_curso.exemplo
        
        self.assertEqual(exemplo, "SG.COODC.123456")

    def test_papel_sigla_unique(self):
        """Testa que sigla deve ser única."""
        with self.assertRaises(IntegrityError):
            Papel.objects.create(
                contexto=Papel.Contexto.PROGRAMA,
                nome="Outro Papel",
                sigla="COODC",  # Sigla duplicada
                papel="outropapel",
                        active=True
            )

    def test_papel_contexto_choices(self):
        """Testa choices de contexto."""
        self.assertEqual(self.papel_curso.contexto, Papel.Contexto.CURSO)
        
        papel_polo = Papel.objects.create(
            contexto=Papel.Contexto.POLO,
            nome="Coord Pólo",
            sigla="CP",
            papel="coordpolo",
                    active=True
        )
        self.assertEqual(papel_polo.contexto, Papel.Contexto.POLO)

    def test_papel_active_field(self):
        """Testa campo active."""
        self.assertTrue(self.papel_curso.active)
        
        self.papel_curso.active = False
        self.papel_curso.save()
        
        papel = Papel.objects.get(pk=self.papel_curso.pk)
        self.assertFalse(papel.active)

    def test_papel_ordering(self):
        """Testa ordenação de papéis."""
        papel_programa = Papel.objects.create(
            contexto=Papel.Contexto.PROGRAMA,
            nome="Coordenador UAB",
            sigla="CUAB",
            papel="coordenadoruab",
                    active=True
        )
        
        papel_polo = Papel.objects.create(
            contexto=Papel.Contexto.POLO,
            nome="Coordenador Pólo",
            sigla="CPOLO",
            papel="coordpolo",
                    active=True
        )
        
        papeis = list(Papel.objects.all())
        # Ordenação: contexto, nome
        self.assertEqual(papeis[0].contexto, Papel.Contexto.CURSO)

    def test_papel_history_tracking(self):
        """Testa histórico de alterações."""
        initial_history_count = self.papel_curso.history.count()
        
        self.papel_curso.nome = "Novo Nome"
        self.papel_curso.save()
        
        self.assertEqual(
            self.papel_curso.history.count(),
            initial_history_count + 1
        )

    def test_papel_verbose_names(self):
        """Testa verbose_name e verbose_name_plural."""
        self.assertEqual(Papel._meta.verbose_name, "papel")
        self.assertEqual(Papel._meta.verbose_name_plural, "papéis")


class CohortModelTestCase(TestCase):
    """Testes para o modelo Cohort."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.papel = Papel.objects.create(
            contexto=Papel.Contexto.CURSO,
            nome="Coordenador de Curso",
            sigla="COODC",
            papel="teachercoordenadorcurso",
                    active=True
        )
        
        self.cohort = Cohort.objects.create(
            name="Test Cohort",
            idnumber="TEST001",
            visible=True,
            papel=self.papel
        )

    def test_create_cohort(self):
        """Testa criação de cohort."""
        cohort = Cohort.objects.create(
            name="New Cohort",
            idnumber="NEW001",
            visible=True,
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

    def test_cohort_visible_field(self):
        """Testa campo visible."""
        self.assertTrue(self.cohort.visible)
        
        self.cohort.visible = False
        self.cohort.save()
        
        cohort = Cohort.objects.get(pk=self.cohort.pk)
        self.assertFalse(cohort.visible)

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
        self.assertEqual(Cohort._meta.verbose_name, "cohort")
        self.assertEqual(Cohort._meta.verbose_name_plural, "cohorts")


class EnrolmentModelTestCase(TestCase):
    """Testes para o modelo Enrolment."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.user = User.objects.create_user(
            username='testuser',
            password='password123'
        )
        
        self.papel = Papel.objects.create(
            contexto=Papel.Contexto.CURSO,
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


class CoorteCursoModelTestCase(TestCase):
    """Testes para o modelo CoorteCurso."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.papel = Papel.objects.create(
            contexto=Papel.Contexto.CURSO,
            nome="Coordenador de Curso",
            sigla="COODC",
            papel="coordcurso",
                    active=True
        )
        
        self.curso = Curso.objects.create(
            suap_id=123,
            codigo="132456",
            nome="Curso de Teste",
            descricao="Descrição do curso"
        )
        
        self.coorte_curso = CoorteCurso.objects.create(
            papel=self.papel,
            curso=self.curso
        )

    def test_create_coorte_curso(self):
        """Testa criação de CoorteCurso."""
        curso2 = Curso.objects.create(
            suap_id=456,
            codigo="654321",
            nome="Outro Curso"
        )
        
        coorte = CoorteCurso.objects.create(
            papel=self.papel,
            curso=curso2
        )
        
        self.assertIsNotNone(coorte.pk)
        self.assertEqual(coorte.curso, curso2)

    def test_coorte_curso_str_representation(self):
        """Testa representação em string de CoorteCurso."""
        string_repr = str(self.coorte_curso)
        
        self.assertIn("ZL", string_repr)
        self.assertIn("COODC", string_repr)
        self.assertIn("132456", string_repr)

    def test_coorte_curso_codigo_property(self):
        """Testa propriedade codigo."""
        # codigo vem de curso.codigo_integracao
        self.assertEqual(self.coorte_curso.codigo, "132456")

    def test_coorte_curso_instancia_property(self):
        """Testa propriedade instancia."""
        self.assertEqual(self.coorte_curso.instancia, self.curso)

    def test_coorte_curso_polymorphic(self):
        """Testa que CoorteCurso é filho de Coorte."""
        self.assertIsInstance(self.coorte_curso, Coorte)
        
        # Busca pelo modelo pai
        coorte = Coorte.objects.get(pk=self.coorte_curso.pk)
        self.assertEqual(coorte.get_real_instance(), self.coorte_curso)

    def test_coorte_curso_validate_unique_constraint(self):
        """Testa validação de unicidade (papel + curso)."""
        duplicate = CoorteCurso(
            papel=self.papel,
            curso=self.curso
        )
        
        with self.assertRaises(ValidationError) as context:
            duplicate.validate_unique()
        
        self.assertIn("curso", context.exception.message_dict)

    def test_coorte_curso_allows_different_papel(self):
        """Testa que permite mesmo curso com papel diferente."""
        papel2 = Papel.objects.create(
            contexto=Papel.Contexto.CURSO,
            nome="Professor",
            sigla="PROF",
            papel="teacher",
                    active=True
        )
        
        coorte2 = CoorteCurso.objects.create(
            papel=papel2,
            curso=self.curso
        )
        
        self.assertIsNotNone(coorte2.pk)
        self.assertNotEqual(coorte2, self.coorte_curso)

    def test_coorte_curso_ordering(self):
        """Testa ordenação de CoorteCurso."""
        curso2 = Curso.objects.create(
            suap_id=456,
            codigo="111111",
            nome="Curso A"
        )
        
        coorte2 = CoorteCurso.objects.create(
            papel=self.papel,
            curso=curso2
        )
        
        coortes = list(CoorteCurso.objects.all())
        # Ordenação por curso
        self.assertEqual(len(coortes), 2)

    def test_coorte_curso_verbose_names(self):
        """Testa verbose_name e verbose_name_plural."""
        self.assertEqual(CoorteCurso._meta.verbose_name, "coortes de curso")
        self.assertEqual(CoorteCurso._meta.verbose_name_plural, "coortes de cursos")


class CoortePoloModelTestCase(TestCase):
    """Testes para o modelo CoortePolo."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.papel = Papel.objects.create(
            contexto=Papel.Contexto.POLO,
            nome="Coordenador de Pólo",
            sigla="COODP",
            papel="coordpolo",
                    active=True
        )
        
        self.polo = Polo.objects.create(
            suap_id=456,
            nome="Pólo Natal (RN)"
        )
        
        self.coorte_polo = CoortePolo.objects.create(
            papel=self.papel,
            polo=self.polo
        )

    def test_create_coorte_polo(self):
        """Testa criação de CoortePolo."""
        polo2 = Polo.objects.create(
            suap_id=789,
            nome="Pólo Mossoró (RN)"
        )
        
        coorte = CoortePolo.objects.create(
            papel=self.papel,
            polo=polo2
        )
        
        self.assertIsNotNone(coorte.pk)
        self.assertEqual(coorte.polo, polo2)

    def test_coorte_polo_str_representation(self):
        """Testa representação em string de CoortePolo."""
        string_repr = str(self.coorte_polo)
        
        self.assertIn("ZL", string_repr)
        self.assertIn("COODP", string_repr)

    def test_coorte_polo_codigo_property(self):
        """Testa propriedade codigo."""
        # codigo vem de polo.codigo_integracao (nome sem caracteres especiais)
        # "Plo Natal/RN" -> "PloNatalRN" (remove espaços e /)
        expected_codigo = "PloNatalRN"
        self.assertEqual(self.coorte_polo.codigo, expected_codigo)

    def test_coorte_polo_instancia_property(self):
        """Testa propriedade instancia."""
        self.assertEqual(self.coorte_polo.instancia, self.polo)

    def test_coorte_polo_polymorphic(self):
        """Testa que CoortePolo é filho de Coorte."""
        self.assertIsInstance(self.coorte_polo, Coorte)
        
        coorte = Coorte.objects.get(pk=self.coorte_polo.pk)
        self.assertEqual(coorte.get_real_instance(), self.coorte_polo)

    def test_coorte_polo_validate_unique_constraint(self):
        """Testa validação de unicidade (papel + polo)."""
        duplicate = CoortePolo(
            papel=self.papel,
            polo=self.polo
        )
        
        with self.assertRaises(ValidationError) as context:
            duplicate.validate_unique()
        
        self.assertIn("polo", context.exception.message_dict)

    def test_coorte_polo_allows_different_papel(self):
        """Testa que permite mesmo pólo com papel diferente."""
        papel2 = Papel.objects.create(
            contexto=Papel.Contexto.POLO,
            nome="Tutor",
            sigla="TUTOR",
            papel="tutor",
                    active=True
        )
        
        coorte2 = CoortePolo.objects.create(
            papel=papel2,
            polo=self.polo
        )
        
        self.assertIsNotNone(coorte2.pk)
        self.assertNotEqual(coorte2, self.coorte_polo)

    def test_coorte_polo_verbose_names(self):
        """Testa verbose_name e verbose_name_plural."""
        self.assertEqual(CoortePolo._meta.verbose_name, "coorte de polo")
        self.assertEqual(CoortePolo._meta.verbose_name_plural, "coortes de polos")


class CoorteProgramaModelTestCase(TestCase):
    """Testes para o modelo CoortePrograma."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.papel = Papel.objects.create(
            contexto=Papel.Contexto.PROGRAMA,
            nome="Coordenador UAB",
            sigla="CUAB",
            papel="coorduab",
                    active=True
        )
        
        self.programa = Programa.objects.create(
            nome="Universidade Aberta do Brasil",
            sigla="UAB"
        )
        
        self.coorte_programa = CoortePrograma.objects.create(
            papel=self.papel,
            programa=self.programa
        )

    def test_create_coorte_programa(self):
        """Testa criação de CoortePrograma."""
        programa2 = Programa.objects.create(
            nome="E-TEC",
            sigla="ETEC"
        )
        
        coorte = CoortePrograma.objects.create(
            papel=self.papel,
            programa=programa2
        )
        
        self.assertIsNotNone(coorte.pk)
        self.assertEqual(coorte.programa, programa2)

    def test_coorte_programa_str_representation(self):
        """Testa representação em string de CoortePrograma."""
        string_repr = str(self.coorte_programa)
        
        self.assertIn("ZL", string_repr)
        self.assertIn("CUAB", string_repr)
        self.assertIn("UAB", string_repr)

    def test_coorte_programa_codigo_property(self):
        """Testa propriedade codigo."""
        # codigo vem de programa.codigo_integracao (sigla)
        self.assertEqual(self.coorte_programa.codigo, "UAB")

    def test_coorte_programa_instancia_property(self):
        """Testa propriedade instancia."""
        self.assertEqual(self.coorte_programa.instancia, self.programa)

    def test_coorte_programa_polymorphic(self):
        """Testa que CoortePrograma é filho de Coorte."""
        self.assertIsInstance(self.coorte_programa, Coorte)
        
        coorte = Coorte.objects.get(pk=self.coorte_programa.pk)
        self.assertEqual(coorte.get_real_instance(), self.coorte_programa)

    def test_coorte_programa_validate_unique_constraint(self):
        """Testa validação de unicidade (papel + programa)."""
        duplicate = CoortePrograma(
            papel=self.papel,
            programa=self.programa
        )
        
        with self.assertRaises(ValidationError) as context:
            duplicate.validate_unique()
        
        self.assertIn("programa", context.exception.message_dict)

    def test_coorte_programa_allows_different_papel(self):
        """Testa que permite mesmo programa com papel diferente."""
        papel2 = Papel.objects.create(
            contexto=Papel.Contexto.PROGRAMA,
            nome="Supervisor",
            sigla="SUPER",
            papel="supervisor",
                    active=True
        )
        
        coorte2 = CoortePrograma.objects.create(
            papel=papel2,
            programa=self.programa
        )
        
        self.assertIsNotNone(coorte2.pk)
        self.assertNotEqual(coorte2, self.coorte_programa)

    def test_coorte_programa_verbose_names(self):
        """Testa verbose_name e verbose_name_plural."""
        self.assertEqual(CoortePrograma._meta.verbose_name, "coortes de programa")
        self.assertEqual(CoortePrograma._meta.verbose_name_plural, "coortes de programas")


class VinculoModelTestCase(TestCase):
    """Testes para o modelo Vinculo."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.user = User.objects.create_user(
            username='testuser',
            password='password123'
        )
        
        self.papel = Papel.objects.create(
            contexto=Papel.Contexto.CURSO,
            nome="Coordenador",
            sigla="COORD",
            papel="coordenador",
                    active=True
        )
        
        self.curso = Curso.objects.create(
            suap_id=123,
            codigo="123456",
            nome="Curso Teste"
        )
        
        self.coorte = CoorteCurso.objects.create(
            papel=self.papel,
            curso=self.curso
        )
        
        self.vinculo = Vinculo.objects.create(
            colaborador=self.user,
            coorte=self.coorte
        )

    def test_create_vinculo(self):
        """Testa criação de vínculo."""
        user2 = User.objects.create_user(
            username='testuser2',
            password='password123'
        )
        
        vinculo = Vinculo.objects.create(
            colaborador=user2,
            coorte=self.coorte
        )
        
        self.assertIsNotNone(vinculo.pk)
        self.assertEqual(vinculo.colaborador, user2)
        self.assertEqual(vinculo.coorte, self.coorte)

    def test_vinculo_str_representation(self):
        """Testa representação em string do vínculo."""
        string_repr = str(self.vinculo)
        
        self.assertIn("testuser", string_repr)
        self.assertIn("ZL", string_repr)

    def test_vinculo_colaborador_relationship(self):
        """Testa relacionamento com User."""
        self.assertEqual(self.vinculo.colaborador, self.user)

    def test_vinculo_coorte_relationship(self):
        """Testa relacionamento com Coorte."""
        self.assertEqual(self.vinculo.coorte, self.coorte)
        self.assertIn(self.vinculo, self.coorte.vinculos.all())

    def test_multiple_vinculos_same_coorte(self):
        """Testa múltiplos vínculos na mesma coorte."""
        user2 = User.objects.create_user(username='user2', password='pass')
        user3 = User.objects.create_user(username='user3', password='pass')
        
        Vinculo.objects.create(colaborador=user2, coorte=self.coorte)
        Vinculo.objects.create(colaborador=user3, coorte=self.coorte)
        
        self.assertEqual(self.coorte.vinculos.count(), 3)

    def test_vinculo_ordering(self):
        """Testa ordenação de vínculos."""
        user2 = User.objects.create_user(username='anotheruser', password='pass')
        Vinculo.objects.create(colaborador=user2, coorte=self.coorte)
        
        vinculos = list(Vinculo.objects.all())
        # Ordenação: coorte, colaborador
        self.assertEqual(len(vinculos), 2)

    def test_vinculo_verbose_names(self):
        """Testa verbose_name e verbose_name_plural."""
        self.assertEqual(Vinculo._meta.verbose_name, "vínculo")
        self.assertEqual(Vinculo._meta.verbose_name_plural, "vínculos")


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
        expected = ["nome", "contexto", "papel", "sigla", "exemplo", "active"]
        self.assertEqual(self.papel_admin.list_display, expected)

    def test_papel_admin_list_filter(self):
        """Testa configuração de list_filter."""
        self.assertIn("active", self.papel_admin.list_filter)
        self.assertIn("contexto", self.papel_admin.list_filter)

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
        expected = ["contexto", "papel", "sigla", "nome", "active"]
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
        expected = ["name", "idnumber", "rule_diario", "rule_coordenacao", "visible"]
        self.assertEqual(self.cohort_admin.list_display, expected)

    def test_cohort_admin_search_fields(self):
        """Testa configuração de search_fields."""
        expected = ["name", "idnumber"]
        self.assertEqual(self.cohort_admin.search_fields, expected)

    def test_cohort_admin_list_filter(self):
        """Testa configuração de list_filter."""
        self.assertIn("visible", self.cohort_admin.list_filter)

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


class PapelFilterTestCase(TestCase):
    """Testes para PapelFilter."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.papel_curso = Papel.objects.create(
            contexto=Papel.Contexto.CURSO,
            nome="Coordenador de Curso",
            sigla="COODC",
            papel="coordcurso",
                    active=True
        )
        
        self.papel_polo = Papel.objects.create(
            contexto=Papel.Contexto.POLO,
            nome="Coordenador de Pólo",
            sigla="COODP",
            papel="coordpolo",
                    active=True
        )
        
        self.curso = Curso.objects.create(
            suap_id=123,
            codigo="123456",
            nome="Curso Teste"
        )
        
        self.coorte_curso = CoorteCurso.objects.create(
            papel=self.papel_curso,
            curso=self.curso
        )

    def test_papel_filter_title(self):
        """Testa título do filtro."""
        filter_instance = PapelFilter(None, {}, Coorte, None)
        self.assertEqual(filter_instance.title, "papel")

    def test_papel_filter_parameter_name(self):
        """Testa parameter_name do filtro."""
        filter_instance = PapelFilter(None, {}, Coorte, None)
        self.assertEqual(filter_instance.parameter_name, "papel")


class IntegrationTestCase(TestCase):
    """Testes de integração para fluxos completos."""

    def test_complete_cohort_workflow(self):
        """Testa fluxo completo: Papel -> Cohort -> Enrolment."""
        # 1. Cria papel
        papel = Papel.objects.create(
            contexto=Papel.Contexto.CURSO,
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

    def test_complete_coorte_workflow(self):
        """Testa fluxo completo: Papel -> CoorteCurso -> Vinculo."""
        # 1. Cria papel
        papel = Papel.objects.create(
            contexto=Papel.Contexto.CURSO,
            nome="Professor",
            sigla="PROF",
            papel="teacher",
                    active=True
        )
        
        # 2. Cria curso
        curso = Curso.objects.create(
            suap_id=999,
            codigo="999999",
            nome="Curso Integração"
        )
        
        # 3. Cria coorte
        coorte = CoorteCurso.objects.create(
            papel=papel,
            curso=curso
        )
        
        # 4. Cria usuário
        user = User.objects.create_user(username='professor', password='pass')
        
        # 5. Cria vínculo
        vinculo = Vinculo.objects.create(
            colaborador=user,
            coorte=coorte
        )
        
        # Verifica relacionamentos
        self.assertEqual(coorte.papel, papel)
        self.assertEqual(coorte.curso, curso)
        self.assertEqual(vinculo.coorte, coorte)
        self.assertEqual(vinculo.colaborador, user)


class EdgeCasesTestCase(TestCase):
    """Testes de casos extremos."""

    def test_coorte_curso_without_pk(self):
        """Testa representação de CoorteCurso sem pk."""
        papel = Papel.objects.create(
            contexto=Papel.Contexto.CURSO,
            nome="Coord",
            sigla="C",
            papel="c",
                    active=True
        )
        
        curso = Curso.objects.create(
            suap_id=1,
            codigo="1",
            nome="C"
        )
        
        coorte = CoorteCurso(papel=papel, curso=curso)
        
        # Sem salvar, não tem pk
        string_repr = str(coorte)
        self.assertIn("sem pk", string_repr)

    def test_papel_exemplo_with_empty_sigla(self):
        """Testa exemplo com sigla vazia."""
        papel = Papel(
            contexto=Papel.Contexto.CURSO,
            nome="Test",
            sigla="",
            papel="test"
        )
        
        exemplo = papel.exemplo
        self.assertEqual(exemplo, "SG..123456")

    def test_cohort_with_null_description(self):
        """Testa cohort com descrição nula."""
        papel = Papel.objects.create(
            contexto=Papel.Contexto.CURSO,
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
            contexto=Papel.Contexto.CURSO,
            nome="Inactive",
            sigla="INAC",
            papel="inactive",
                    active=False
        )
        
        string_repr = str(papel)
        self.assertIn("⛔", string_repr)

    def test_coorte_codigo_property_through_polymorphic(self):
        """Testa propriedade codigo através do modelo polimórfico."""
        papel = Papel.objects.create(
            contexto=Papel.Contexto.CURSO,
            nome="Test",
            sigla="T",
            papel="test",
                    active=True
        )
        
        curso = Curso.objects.create(
            suap_id=1,
            codigo="123",
            nome="C"
        )
        
        coorte_curso = CoorteCurso.objects.create(
            papel=papel,
            curso=curso
        )
        
        # Acessa através do modelo pai
        coorte = Coorte.objects.get(pk=coorte_curso.pk)
        
        # Propriedade codigo deve funcionar através de get_real_instance()
        self.assertEqual(coorte.codigo, "123")
