from django.utils.translation import gettext as _
from django.db.models import CharField, BooleanField, ForeignKey, PROTECT, TextField
from django.db.models import Model
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from base.models import ActiveMixin
from django_rule_engine.fields import RuleField


JSON_DE_EXEMPLO = {
    "polo": {
        "id": 3,
        "descricao": "Nome do polo (RN)"
    },
    "curso": {
        "id": 123,
        "nome": "Curso de Formação Inicial e Continuada (FIC) ou Qualificação Profissional em Alguma Coisa Aí",
        "codigo": "132456",
        "descricao": "FIC+ em Alguma Coisa Aí"
    },
    "turma": {
        "id": 1234,
        "codigo": "20261.1.132456.123.1M"
    },
    "alunos": [
        {
        "id": 1,
        "nome": "Aluno um",
        "polo": {
            "id": 3,
            "descricao": "Nome do polo (RN)"
        },
        "email": "",
        "programa": "UAB",
        "situacao": "ativo",
        "matricula": "20261132456RN0001",
        "situacao_diario": "ativo",
        "email_secundario": "aluno1@teste.local"
        }            
    ],
    "campus": {
        "id": 1,
        "sigla": "CENTRAL",
        "descricao": "CAMPUS CENTRAL"
    },
    "diario": {
        "id": 123456,
        "tipo": "regular",
        "sigla": "FIC.1234",
        "situacao": "Aberto",
        "descricao": "Matemática",
        "descricao_historico": "Matemática"
    },
    "componente": {
        "id": 4321,
        "tipo": 1,
        "sigla": "FIC.1234",
        "periodo": 1,
        "optativo": False,
        "descricao": "Matemática",
        "qtd_avaliacoes": 1,
        "descricao_historico": "Matemática"
    },
    "professores": [
        {
            "id": 11,
            "nome": "Professor onze",
            "tipo": "Principal",
            "email": "professor.onze@email.local",
            "login": "12345611",
            "status": "ativo",
            "email_secundario": "professor.onze@email.local"
        },
        {
            "id": 12,
            "nome": "Professor doze",
            "tipo": "Formador",
            "email": "professor.doze@email.local",
            "login": "12345612",
            "status": "ativo",
            "email_secundario": "professor.doze@email.local"
        },
        {
            "id": 13,
            "nome": "Professor treze",
            "tipo": "Tutor",
            "email": "professor.treze@email.local",
            "login": "12345613",
            "status": "ativo",
            "email_secundario": "professor.treze@email.local"
        },
        {
            "id": 14,
            "nome": "Professor quatorze",
            "tipo": "Mediador",
            "email": "professor.quatorze@email.local",
            "login": "12345614",
            "status": "inativo",
            "email_secundario": "professor.quatorze@email.local"
        }
    ]
}


class Papel(ActiveMixin, Model):

    nome = CharField(
        _("nome da coorte"),
        max_length=256,
        help_text="Este atributo será cohort.name"
        " Ex.: <sup>Coordenador de curso</sup>, <sup>Coordenador de pólo</sup>, <sup>Coordenador de UAB</sup>.",
    )
    sigla = CharField(
        _("sufixo do corteid coorte"),
        max_length=10,
        blank=False,
        null=False,
        unique=True,
        help_text=_(
            "Este atributo será o sufixo da cohort.idnumber,"
            " ({campus.sigla}.{este_sufixo}.{curso.instancia.codigo})."
            " Ex.: <sup>COODC</sup>, <sup>COODP</sup>, <sup>COODUAB</sup>"
        ),
    )
    papel = CharField(
        _("nome do papel (role) no curso"),
        max_length=256,
        help_text=_(
            "Este atributo deve ser conforme role.shortname."
            " Ex.: <sup>teachercoordenadorcurso</sup>, <sup>coordenadordepolo</sup>, <sup>coordenadordeprograma</sup>"
        ),
    )
    active = BooleanField(_("ativo?"), help_text=_("Indica se esta coorte deverá ser sincronizada"))

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("papel")
        verbose_name_plural = _("papéis")
        ordering = ["nome"]

    @property
    def exemplo(self):
        return f"SG.{self.sigla}.123456"

    def __str__(self):
        sigla = f"{self.sigla}" if self.sigla else ""
        return f"{self.nome} {self.active_icon}"


class Cohort(ActiveMixin, Model):
    name = CharField(_("nome da coorte"), max_length=2560, unique=True)
    idnumber = CharField(_("idnumber"), max_length=2560, unique=True)
    active = BooleanField(_("visível"), default=True)
    papel = ForeignKey(Papel, on_delete=PROTECT, related_name="cohort_papel")
    rule_diario = RuleField(
        _("regra de validação para diário"),
        blank=True,
        null=True,
        example_data=JSON_DE_EXEMPLO,
        help_text="Exemplos: <ul><li>curso.codigo == '132456'</li></ul>"
    )
    rule_coordenacao = RuleField(
        _("regra de validação para sala de coordenação"),
        blank=True,
        null=True,
        example_data=JSON_DE_EXEMPLO,
    )
    description = TextField(_("Descrição"), null=True, blank=True)

    class Meta:
        verbose_name = _("coorte")
        verbose_name_plural = _("coortes")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Enrolment(Model):
    colaborador = ForeignKey(User, on_delete=PROTECT)
    cohort = ForeignKey(Cohort, on_delete=PROTECT, related_name="enrolments")

    class Meta:
        verbose_name = _("vínculo")
        verbose_name_plural = _("vínculos")
        ordering = ["cohort", "colaborador"]

    def __str__(self):
        return f"{self.colaborador.username} ({self.colaborador.get_full_name()}) em {self.cohort}"
