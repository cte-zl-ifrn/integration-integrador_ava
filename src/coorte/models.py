from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.db.models import CharField, BooleanField, ForeignKey, PROTECT
from django.db.models import Model
from django.contrib.auth.models import User
from django_better_choices import Choices
from simple_history.models import HistoricalRecords
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


class Coorte(PolymorphicModel):
    papel = ForeignKey(Papel, on_delete=PROTECT, related_name="coorte_papel")

    class Meta:
        verbose_name = _("Coorte")
        verbose_name_plural = _("Coortes")
        ordering = ["papel"]

    def __str__(self):
        return f"SG.{self.papel.sigla}.{self.codigo}"

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
        return f"SG.{self.papel.sigla}.{self.codigo}"


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
