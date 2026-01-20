from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.db.models import CharField, BooleanField, ForeignKey, PROTECT, TextField
from django.db.models import Model
from django.contrib.auth.models import User
from django_better_choices import Choices
from simple_history.models import HistoricalRecords
from polymorphic.models import PolymorphicModel
from base.models import ActiveMixin
from django_rule_engine.fields import RuleField
from edu.models import Curso, Polo, Programa


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



def dados_vinculo(vinculo):
    return {
        "login": vinculo.colaborador.username,
        "email": vinculo.colaborador.email,
        "nome": vinculo.colaborador.get_full_name(),
        "status": "Ativo" if vinculo.coorte.papel.active else "Inativo",
    }


class Papel(ActiveMixin, Model):
    class Contexto(Choices):
        CURSO = Choices.Value(_("Curso"), value="curso")
        POLO = Choices.Value(_("Pólo"), value="polo")
        PROGRAMA = Choices.Value(_("Programa"), value="programa")

    contexto = CharField(
        _("aplica-se a"),
        max_length=256,
        choices=Contexto,
        default=Contexto.CURSO,
        help_text="Limita em qual contexto pode ocorrer a ação",
    )
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
        ordering = ["contexto", "nome"]

    @property
    def exemplo(self):
        return f"SG.{self.sigla}.123456"

    def __str__(self):
        sigla = f"{self.sigla}" if self.sigla else ""
        return f"{self.nome} {self.active_icon}"


class Cohort(ActiveMixin, Model):
    name = CharField(_("nome da coorte"), max_length=2560, unique=True)
    idnumber = CharField(_("idnumber"), max_length=2560, unique=True)
    visible = BooleanField(_("visível"), default=True)
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
        verbose_name = _("cohort")
        verbose_name_plural = _("cohorts")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Coorte(PolymorphicModel):
    papel = ForeignKey(Papel, on_delete=PROTECT, related_name="coorte_papel")

    class Meta:
        verbose_name = _("Coorte")
        verbose_name_plural = _("Coortes")
        ordering = ["papel"]

    def __str__(self):
        return f"CAMPUS.{self.papel.sigla}.{self.codigo}"

    @property
    def codigo(self):
        return self.get_real_instance().codigo


class CoorteCurso(Coorte):
    curso = ForeignKey(Curso, on_delete=PROTECT, related_name="coorte_curso")

    class Meta:
        verbose_name = _("coortes de curso")
        verbose_name_plural = _("coortes de cursos")
        ordering = ["curso"]

    @property
    def instancia(self):
        return self.curso

    @property
    def codigo(self):
        return self.instancia.codigo_integracao

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude=exclude)
        if not self.papel_id or not self.curso_id:
            return
        qs = type(self).objects.filter(papel=self.papel, curso=self.curso)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError(
                {"curso": _("Já existe uma CoorteCurso com esse papel e curso.")}
            )
    def __str__(self):
        if not self.pk:
            return f"CoorteCurso (sem pk)"
        return f"CAMPUS.{self.papel.sigla}.{self.codigo}"


class CoortePolo(Coorte):
    polo = ForeignKey(Polo, on_delete=PROTECT, related_name="coorte_polo")

    class Meta:
        verbose_name = _("coorte de polo")
        verbose_name_plural = _("coortes de polos")
        ordering = ["polo"]

    @property
    def instancia(self):
        return self.polo

    @property
    def codigo(self):
        return self.instancia.codigo_integracao

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude=exclude)
        if not self.papel_id or not self.polo_id:
            return
        qs = type(self).objects.filter(papel=self.papel, polo=self.polo)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError(
                {"polo": _("Já existe uma CoortePolo com esse papel e polo.")}
            )


class CoortePrograma(Coorte):
    programa = ForeignKey(Programa, on_delete=PROTECT, related_name="coorte_programa")

    class Meta:
        verbose_name = _("coortes de programa")
        verbose_name_plural = _("coortes de programas")
        ordering = ["programa"]

    @property
    def instancia(self):
        return self.programa

    @property
    def codigo(self):
        return self.instancia.codigo_integracao

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude=exclude)
        if not self.papel_id or not self.programa_id:
            return
        qs = type(self).objects.filter(papel=self.papel, programa=self.programa)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError(
                {"programa": _("Já existe uma CoortePrograma com esse papel e programa.")}
            )


class Vinculo(Model):
    colaborador = ForeignKey(User, on_delete=PROTECT)
    coorte = ForeignKey(Coorte, on_delete=PROTECT, related_name="vinculos")

    class Meta:
        verbose_name = _("vínculo")
        verbose_name_plural = _("vínculos")
        ordering = ["coorte", "colaborador"]

    def __str__(self):
        return f"{self.colaborador.username} ({self.colaborador.get_full_name()}) em {self.coorte}"
