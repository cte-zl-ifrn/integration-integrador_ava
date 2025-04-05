from django.utils.translation import gettext as _
from django.db.models import (
    CharField,
    DateTimeField,
    JSONField,
    BooleanField,
    ForeignKey,
    PROTECT,
)
from django.db.models import Manager, Model, QuerySet, Q
from django.contrib.auth.models import User
from django_better_choices import Choices
from simple_history.models import HistoricalRecords
from django.utils.html import format_html
from polymorphic.models import PolymorphicModel
from base.models import ActiveMixin
from edu.models import Curso, Polo, Programa

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
        help_text="Limita em qual contexto pode ocorrer a ação"
    )
    nome = CharField(
        _("nome da coorte"),
        max_length=256,
        help_text="Este atributo será cohort.name"
                  " Ex.: <sup>Coordenador de curso</sup>, <sup>Coordenador de pólo</sup>, <sup>Coordenador de UAB</sup>."
    )
    sigla = CharField(
        _("sufixo do corteid coorte"),
        max_length=10,
        blank=True,
        null=False,
        unique=True,
        help_text=_("Este atributo será o sufixo da cohort.idnumber,"
                  " ({campus.sigla}.{curso.instanceia.codigo}.{este_sufixo})."
                    " Ex.: <sup>COODC</sup>, <sup>COODP</sup>, <sup>COODUAB</sup>")
    )
    papel = CharField(
        _("nome do papel (role) no curso"),
        max_length=256,
        help_text=_("Este atributo deve ser conforme role.shortname."
                    " Ex.: <sup>teachercoordenadorcurso</sup>, <sup>coordenadordepolo</sup>, <sup>coordenadordeprograma</sup>")
    )
    active = BooleanField(_("ativo?"), help_text=_("Indica se esta coorte deverá ser sincronizada"))

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("papel")
        verbose_name_plural = _("papéis")
        ordering = ["nome"]

    @property
    def codigo(self):
        return f".{self.sigla}" if self.sigla else ""

    def __str__(self):
        sigla = f"{self.sigla}" if self.sigla else ""
        return f"{self.nome} (CAMPUS.INSTANCIA.{sigla}) {self.active_icon}"


class Coorte(PolymorphicModel):
    papel = ForeignKey(Papel, on_delete=PROTECT, related_name='coorte_papel')

    def __str__(self):
        return f"{self.id} - {self.papel}"

    class Meta:
        verbose_name = _("Coorte")
        verbose_name_plural = _("Coortes")
        ordering = ["papel"]


class CoorteCurso(Coorte):
    curso = ForeignKey(Curso, on_delete=PROTECT, related_name="coorte_curso")

    class Meta:
        verbose_name = _("Coorte x Curso")
        verbose_name_plural = _("Coorte x Curso")
        ordering = ["curso"]


class CoortePolo(Coorte):
    polo = ForeignKey(Polo, on_delete=PROTECT, related_name="coorte_polo")

    class Meta:
        verbose_name = _("Coorte x Polo")
        verbose_name_plural = _("Coorte x Polo")
        ordering = ["polo"]


class CoortePrograma(Coorte):
    programa = ForeignKey(Programa, on_delete=PROTECT, related_name="coorte_programa")

    class Meta:
        verbose_name = _("Coorte x Programa")
        verbose_name_plural = _("Coorte x Programa")
        ordering = ["programa"]


class Vinculo(Model):
    colaborador = ForeignKey(User, on_delete=PROTECT)
    coorte = ForeignKey(Coorte, on_delete=PROTECT, related_name="vinculos")
