from django.utils.translation import gettext as _
import re
from django.db.models import CharField
from django.db.models import Model
from simple_history.models import HistoricalRecords


class Curso(Model):
    suap_id = CharField(_("ID do curso no SUAP"), max_length=255, unique=True)
    codigo = CharField(_("código do curso"), max_length=255, unique=True)
    nome = CharField(_("nome do curso"), max_length=255)
    descricao = CharField(_("descrição"), max_length=255)

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("curso")
        verbose_name_plural = _("cursos")
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.codigo})"

    @property
    def codigo_integracao(self):
        return self.codigo


class Polo(Model):
    suap_id = CharField(_("ID do pólo no SUAP"), max_length=255, unique=True)
    codigo = CharField(_("sigla do pólo"), max_length=255, unique=True)
    nome = CharField(_("nome do pólo"), max_length=255, unique=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("pólo")
        verbose_name_plural = _("pólos")
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome}"

    @property
    def codigo_integracao(self):
        return re.sub(r'[^a-zA-Z]', '', self.codigo)


class Programa(Model):
    suap_id = CharField(_("ID do programa no SUAP"), max_length=255, unique=False, null=True, blank=True)
    nome = CharField(_("nome do programa"), max_length=255, unique=True)
    sigla = CharField(_("sigla do programa"), max_length=255, unique=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("programa")
        verbose_name_plural = _("programas")
        ordering = ["nome"]

    def __str__(self):
        return self.sigla

    @property
    def codigo_integracao(self):
        return self.sigla
