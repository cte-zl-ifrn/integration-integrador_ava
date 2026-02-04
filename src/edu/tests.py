"""
Testes unitários para a app edu.

Este módulo contém testes para:
- Curso: Modelo de cursos
- Polo: Modelo de polos
- Programa: Modelo de programas
- Properties de código_integracao
- Histórico (simple_history)
- Validações e constraints
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import CharField
from edu.models import Curso, Polo, Programa
from edu.apps import IntegradorConfig


class CursoModelTestCase(TestCase):
    """Testes para o modelo Curso."""

    def setUp(self):
        """Configura dados de teste."""
        self.curso_data = {
            'suap_id': '12345',
            'codigo': 'TEC001',
            'nome': 'Técnico em Informática',
            'descricao': 'Curso técnico em informática para internet'
        }

    def test_create_curso(self):
        """Testa criação de um curso."""
        curso = Curso.objects.create(**self.curso_data)
        
        self.assertEqual(curso.suap_id, '12345')
        self.assertEqual(curso.codigo, 'TEC001')
        self.assertEqual(curso.nome, 'Técnico em Informática')
        self.assertEqual(curso.descricao, 'Curso técnico em informática para internet')

    def test_curso_str_representation(self):
        """Testa representação string do curso."""
        curso = Curso.objects.create(**self.curso_data)
        
        expected = "Técnico em Informática (TEC001)"
        self.assertEqual(str(curso), expected)

    def test_curso_codigo_integracao_property(self):
        """Testa a property codigo_integracao."""
        curso = Curso.objects.create(**self.curso_data)
        
        self.assertEqual(curso.codigo_integracao, curso.codigo)
        self.assertEqual(curso.codigo_integracao, 'TEC001')

    def test_curso_suap_id_unique_constraint(self):
        """Testa constraint de unicidade do suap_id."""
        Curso.objects.create(**self.curso_data)
        
        # Tenta criar outro curso com mesmo suap_id
        with self.assertRaises(IntegrityError):
            Curso.objects.create(
                suap_id='12345',
                codigo='TEC002',
                nome='Outro Curso',
                descricao='Descrição'
            )

    def test_curso_codigo_unique_constraint(self):
        """Testa constraint de unicidade do codigo."""
        Curso.objects.create(**self.curso_data)
        
        # Tenta criar outro curso com mesmo codigo
        with self.assertRaises(IntegrityError):
            Curso.objects.create(
                suap_id='54321',
                codigo='TEC001',
                nome='Outro Curso',
                descricao='Descrição'
            )

    def test_curso_ordering(self):
        """Testa ordenação padrão por nome."""
        Curso.objects.create(suap_id='1', codigo='C1', nome='Zeta', descricao='Desc')
        Curso.objects.create(suap_id='2', codigo='C2', nome='Alpha', descricao='Desc')
        Curso.objects.create(suap_id='3', codigo='C3', nome='Beta', descricao='Desc')
        
        cursos = list(Curso.objects.all())
        
        self.assertEqual(cursos[0].nome, 'Alpha')
        self.assertEqual(cursos[1].nome, 'Beta')
        self.assertEqual(cursos[2].nome, 'Zeta')

    def test_curso_verbose_names(self):
        """Testa verbose_name e verbose_name_plural."""
        self.assertEqual(Curso._meta.verbose_name, 'curso')
        self.assertEqual(Curso._meta.verbose_name_plural, 'cursos')

    def test_curso_has_history(self):
        """Testa se o curso tem histórico (simple_history)."""
        curso = Curso.objects.create(**self.curso_data)
        
        self.assertTrue(hasattr(curso, 'history'))
        self.assertEqual(curso.history.count(), 1)
        
        # Atualiza e verifica histórico
        curso.nome = 'Nome Atualizado'
        curso.save()
        
        self.assertEqual(curso.history.count(), 2)

    def test_curso_field_types(self):
        """Testa tipos dos campos."""
        curso = Curso.objects.create(**self.curso_data)
        
        self.assertIsInstance(curso._meta.get_field('suap_id'), CharField)
        self.assertIsInstance(curso._meta.get_field('codigo'), CharField)
        self.assertIsInstance(curso._meta.get_field('nome'), CharField)
        self.assertIsInstance(curso._meta.get_field('descricao'), CharField)

    def test_curso_max_lengths(self):
        """Testa max_length dos campos."""
        self.assertEqual(Curso._meta.get_field('suap_id').max_length, 255)
        self.assertEqual(Curso._meta.get_field('codigo').max_length, 255)
        self.assertEqual(Curso._meta.get_field('nome').max_length, 255)
        self.assertEqual(Curso._meta.get_field('descricao').max_length, 255)


class PoloModelTestCase(TestCase):
    """Testes para o modelo Polo."""

    def setUp(self):
        """Configura dados de teste."""
        self.polo_data = {
            'suap_id': '99',
            'nome': 'Polo Natal - RN'
        }

    def test_create_polo(self):
        """Testa criação de um polo."""
        polo = Polo.objects.create(**self.polo_data)
        
        self.assertEqual(polo.suap_id, '99')
        self.assertEqual(polo.nome, 'Polo Natal - RN')

    def test_polo_str_representation(self):
        """Testa representação string do polo."""
        polo = Polo.objects.create(**self.polo_data)
        
        self.assertEqual(str(polo), 'Polo Natal - RN')

    def test_polo_codigo_integracao_removes_non_alpha(self):
        """Testa que codigo_integracao remove caracteres não-alfabéticos."""
        polo = Polo.objects.create(**self.polo_data)
        
        # "Polo Natal - RN" -> "PoloNatalRN"
        expected = 'PoloNatalRN'
        self.assertEqual(polo.codigo_integracao, expected)

    def test_polo_codigo_integracao_with_numbers_and_spaces(self):
        """Testa codigo_integracao com números e espaços."""
        polo = Polo.objects.create(suap_id='1', nome='Polo 123 Test - 456')
        
        # Remove números, espaços e caracteres especiais
        self.assertEqual(polo.codigo_integracao, 'PoloTest')

    def test_polo_codigo_integracao_with_special_chars(self):
        """Testa codigo_integracao com caracteres especiais."""
        polo = Polo.objects.create(suap_id='2', nome='Polo São José!')
        
        # Remove caracteres especiais e acentos (ã, é, etc)
        self.assertEqual(polo.codigo_integracao, 'PoloSoJos')

    def test_polo_suap_id_unique_constraint(self):
        """Testa constraint de unicidade do suap_id."""
        Polo.objects.create(**self.polo_data)
        
        with self.assertRaises(IntegrityError):
            Polo.objects.create(suap_id='99', nome='Outro Polo')

    def test_polo_nome_unique_constraint(self):
        """Testa constraint de unicidade do nome."""
        Polo.objects.create(**self.polo_data)
        
        with self.assertRaises(IntegrityError):
            Polo.objects.create(suap_id='100', nome='Polo Natal - RN')

    def test_polo_ordering(self):
        """Testa ordenação padrão por nome."""
        Polo.objects.create(suap_id='1', nome='Zeta Polo')
        Polo.objects.create(suap_id='2', nome='Alpha Polo')
        Polo.objects.create(suap_id='3', nome='Beta Polo')
        
        polos = list(Polo.objects.all())
        
        self.assertEqual(polos[0].nome, 'Alpha Polo')
        self.assertEqual(polos[1].nome, 'Beta Polo')
        self.assertEqual(polos[2].nome, 'Zeta Polo')

    def test_polo_verbose_names(self):
        """Testa verbose_name e verbose_name_plural."""
        self.assertEqual(Polo._meta.verbose_name, 'pólo')
        self.assertEqual(Polo._meta.verbose_name_plural, 'pólos')

    def test_polo_has_history(self):
        """Testa se o polo tem histórico."""
        polo = Polo.objects.create(**self.polo_data)
        
        self.assertTrue(hasattr(polo, 'history'))
        self.assertEqual(polo.history.count(), 1)


class ProgramaModelTestCase(TestCase):
    """Testes para o modelo Programa."""

    def setUp(self):
        """Configura dados de teste."""
        self.programa_data = {
            'nome': 'Universidade Aberta do Brasil',
            'sigla': 'UAB'
        }

    def test_create_programa(self):
        """Testa criação de um programa."""
        programa = Programa.objects.create(**self.programa_data)
        
        self.assertEqual(programa.nome, 'Universidade Aberta do Brasil')
        self.assertEqual(programa.sigla, 'UAB')

    def test_programa_str_representation(self):
        """Testa representação string do programa."""
        programa = Programa.objects.create(**self.programa_data)
        
        # str retorna a sigla
        self.assertEqual(str(programa), 'UAB')

    def test_programa_codigo_integracao_is_sigla(self):
        """Testa que codigo_integracao é a sigla."""
        programa = Programa.objects.create(**self.programa_data)
        
        self.assertEqual(programa.codigo_integracao, programa.sigla)
        self.assertEqual(programa.codigo_integracao, 'UAB')

    def test_programa_nome_unique_constraint(self):
        """Testa constraint de unicidade do nome."""
        Programa.objects.create(**self.programa_data)
        
        with self.assertRaises(IntegrityError):
            Programa.objects.create(
                nome='Universidade Aberta do Brasil',
                sigla='UAB2'
            )

    def test_programa_sigla_unique_constraint(self):
        """Testa constraint de unicidade da sigla."""
        Programa.objects.create(**self.programa_data)
        
        with self.assertRaises(IntegrityError):
            Programa.objects.create(
                nome='Outro Programa',
                sigla='UAB'
            )

    def test_programa_ordering(self):
        """Testa ordenação padrão por nome."""
        Programa.objects.create(nome='Zeta Programa', sigla='ZP')
        Programa.objects.create(nome='Alpha Programa', sigla='AP')
        Programa.objects.create(nome='Beta Programa', sigla='BP')
        
        programas = list(Programa.objects.all())
        
        self.assertEqual(programas[0].nome, 'Alpha Programa')
        self.assertEqual(programas[1].nome, 'Beta Programa')
        self.assertEqual(programas[2].nome, 'Zeta Programa')

    def test_programa_verbose_names(self):
        """Testa verbose_name e verbose_name_plural."""
        self.assertEqual(Programa._meta.verbose_name, 'programa')
        self.assertEqual(Programa._meta.verbose_name_plural, 'programas')

    def test_programa_has_history(self):
        """Testa se o programa tem histórico."""
        programa = Programa.objects.create(**self.programa_data)
        
        self.assertTrue(hasattr(programa, 'history'))
        self.assertEqual(programa.history.count(), 1)

    def test_programa_field_types(self):
        """Testa tipos dos campos."""
        programa = Programa.objects.create(**self.programa_data)
        
        self.assertIsInstance(programa._meta.get_field('nome'), CharField)
        self.assertIsInstance(programa._meta.get_field('sigla'), CharField)

    def test_programa_max_lengths(self):
        """Testa max_length dos campos."""
        self.assertEqual(Programa._meta.get_field('nome').max_length, 255)
        self.assertEqual(Programa._meta.get_field('sigla').max_length, 255)


class EduAppConfigTestCase(TestCase):
    """Testes para a configuração da app edu."""

    def test_app_config_name(self):
        """Testa se o nome da app está correto."""
        self.assertEqual(IntegradorConfig.name, 'edu')

    def test_app_config_default_auto_field(self):
        """Testa se default_auto_field está configurado."""
        self.assertEqual(
            IntegradorConfig.default_auto_field,
            'django.db.models.BigAutoField'
        )

    def test_app_config_icon(self):
        """Testa se o ícone está definido."""
        self.assertEqual(IntegradorConfig.icon, 'fa fa-home')


class IntegrationTestCase(TestCase):
    """Testes de integração entre os modelos."""

    def test_create_complete_educational_structure(self):
        """Testa criação de estrutura educacional completa."""
        # Cria um programa
        programa = Programa.objects.create(
            nome='Programa de Educação a Distância',
            sigla='EAD'
        )
        
        # Cria um polo
        polo = Polo.objects.create(
            suap_id='1',
            nome='Polo Natal'
        )
        
        # Cria um curso
        curso = Curso.objects.create(
            suap_id='100',
            codigo='TEC001',
            nome='Técnico em Informática',
            descricao='Curso técnico'
        )
        
        # Verifica que todos foram criados
        self.assertEqual(Programa.objects.count(), 1)
        self.assertEqual(Polo.objects.count(), 1)
        self.assertEqual(Curso.objects.count(), 1)

    def test_codigo_integracao_consistency(self):
        """Testa consistência das properties codigo_integracao."""
        curso = Curso.objects.create(
            suap_id='1',
            codigo='TEST123',
            nome='Test Course',
            descricao='Desc'
        )
        
        polo = Polo.objects.create(
            suap_id='2',
            nome='Test Polo 123'
        )
        
        programa = Programa.objects.create(
            nome='Test Program',
            sigla='TP'
        )
        
        # Verifica que todas as properties retornam strings
        self.assertIsInstance(curso.codigo_integracao, str)
        self.assertIsInstance(polo.codigo_integracao, str)
        self.assertIsInstance(programa.codigo_integracao, str)
        
        # Verifica que não são vazias
        self.assertGreater(len(curso.codigo_integracao), 0)
        self.assertGreater(len(polo.codigo_integracao), 0)
        self.assertGreater(len(programa.codigo_integracao), 0)


class EdgeCasesTestCase(TestCase):
    """Testes de casos extremos."""

    def test_polo_codigo_integracao_only_special_chars(self):
        """Testa codigo_integracao quando nome tem apenas caracteres especiais."""
        polo = Polo.objects.create(suap_id='1', nome='123-456!@#')
        
        # Deve retornar string vazia
        self.assertEqual(polo.codigo_integracao, '')

    def test_polo_codigo_integracao_empty_after_removal(self):
        """Testa codigo_integracao com nome que vira vazio após remoção."""
        polo = Polo.objects.create(suap_id='2', nome='   ')
        
        # Nome só com espaços resulta em string vazia
        self.assertEqual(polo.codigo_integracao, '')

    def test_curso_with_empty_strings(self):
        """Testa curso com strings vazias onde permitido."""
        curso = Curso.objects.create(
            suap_id='1',
            codigo='CODE',
            nome='Nome',
            descricao=''  # Vazio
        )
        
        self.assertEqual(curso.descricao, '')

    def test_programa_with_short_sigla(self):
        """Testa programa com sigla curta."""
        programa = Programa.objects.create(
            nome='Test',
            sigla='A'
        )
        
        self.assertEqual(programa.sigla, 'A')
        self.assertEqual(programa.codigo_integracao, 'A')

    def test_curso_update_maintains_codigo_integracao(self):
        """Testa que atualização mantém codigo_integracao consistente."""
        curso = Curso.objects.create(
            suap_id='1',
            codigo='ORIG',
            nome='Original',
            descricao='Desc'
        )
        
        original_codigo = curso.codigo_integracao
        
        # Atualiza outros campos
        curso.nome = 'Atualizado'
        curso.descricao = 'Nova descrição'
        curso.save()
        
        curso.refresh_from_db()
        
        # codigo_integracao deve ser o mesmo (baseado em codigo)
        self.assertEqual(curso.codigo_integracao, original_codigo)

    def test_bulk_create_cursos(self):
        """Testa criação em massa de cursos."""
        cursos = [
            Curso(suap_id=f'{i}', codigo=f'C{i}', nome=f'Curso {i}', descricao='Desc')
            for i in range(10)
        ]
        
        Curso.objects.bulk_create(cursos)
        
        self.assertEqual(Curso.objects.count(), 10)

    def test_history_tracking_on_update(self):
        """Testa rastreamento de histórico em atualizações."""
        curso = Curso.objects.create(
            suap_id='1',
            codigo='TEST',
            nome='Original',
            descricao='Desc'
        )
        
        # Múltiplas atualizações
        for i in range(5):
            curso.nome = f'Nome {i}'
            curso.save()
        
        # Deve ter 6 entradas no histórico (1 criação + 5 atualizações)
        self.assertEqual(curso.history.count(), 6)

    def test_polo_with_unicode_characters(self):
        """Testa polo com caracteres unicode."""
        polo = Polo.objects.create(
            suap_id='1',
            nome='Pólo São José - Açú'
        )
        
        # Verifica que salva corretamente
        self.assertIn('Pólo', polo.nome)
        self.assertIn('São', polo.nome)
        self.assertIn('Açú', polo.nome)
