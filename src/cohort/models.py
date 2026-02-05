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


class Role(ActiveMixin, Model):

    name = CharField(
        _("nome da role"),
        max_length=256,
        help_text="Este atributo será cohort.name"
        " Ex.: <sup>Coordenador de curso</sup>, <sup>Coordenador de pólo</sup>, <sup>Coordenador de UAB</sup>.",
    )
    shortname = CharField(
        _("shortname da role"),
        max_length=256,
        help_text=_(
            "Este atributo deve ser conforme role.shortname."
            " Ex.: <sup>teachercoordenadorcurso</sup>, <sup>coordenadordepolo</sup>, <sup>coordenadordeprograma</sup>"
        ),
    )
    active = BooleanField(_("ativo?"), help_text=_("Indica se esta coorte deverá ser sincronizada"))

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("role")
        verbose_name_plural = _("roles")
        ordering = ["name"]


    def __str__(self):
        return f"{self.name} {self.active_icon}"


class Cohort(ActiveMixin, Model):
    name = CharField(_("nome da coorte"), max_length=2560, unique=True)
    idnumber = CharField(_("idnumber"), max_length=2560, unique=True)
    active = BooleanField(_("visível"), default=True)
    role = ForeignKey(Role, on_delete=PROTECT, related_name="cohort_roles")
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
    user = ForeignKey(User, on_delete=PROTECT, related_name="enrolments")
    cohort = ForeignKey(Cohort, on_delete=PROTECT, related_name="enrolments")

    class Meta:
        verbose_name = _("vínculo")
        verbose_name_plural = _("vínculos")
        ordering = ["cohort", "user"]

    def __str__(self):
        return f"{self.user.username} ({self.user.get_full_name()}) em {self.cohort}"