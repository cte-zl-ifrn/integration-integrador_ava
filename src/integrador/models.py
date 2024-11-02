from django.utils.translation import gettext as _
from django.utils.safestring import mark_safe
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


class ActiveMixin:
    @property
    def active_icon(self):
        return "✅" if self.active else "⛔"


class Contexto(Choices):
    CURSO = Choices.Value(_("Curso"), value="c")
    POLO = Choices.Value(_("Pólo"), value="p")


class Ambiente(Model):
    def _c(color: str):
        return f"""<span style='background: {color}; color: #fff; padding: 1px 5px; font-size: 95%; border-radius: 4px;'>{color}</span>"""

    nome = CharField(_("nome do ambiente"), max_length=255)
    url = CharField(_("URL"), max_length=255)
    token = CharField(_("token"), max_length=255)
    active = BooleanField(_("ativo?"), default=True)

    class Meta:
        verbose_name = _("ambiente")
        verbose_name_plural = _("ambientes")
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome}"

    @property
    def base_url(self):
        return self.url if self.url[-1:] != "/" else self.url[:-1]

    @property
    def base_api_url(self):
        return f"{self.base_url}/local/suap/api"


class Campus(Model):
    suap_id = CharField(_("ID do campus no SUAP"), max_length=255, unique=True)
    sigla = CharField(_("sigla do campus"), max_length=255, unique=True)
    ambiente = ForeignKey(Ambiente, on_delete=PROTECT)
    active = BooleanField(_("ativo?"))

    class Meta:
        verbose_name = _("campus")
        verbose_name_plural = _("campi")
        ordering = ["sigla"]

    def __str__(self):
        return self.sigla

    @property
    def sync_up_enrolments_url(self):
        return f"{self.ambiente.url}/local/suap/api/?sync_up_enrolments"

    @property
    def credentials(self):
        return {"Authentication": f"Token {self.ambiente.token}"}


class Papel(ActiveMixin, Model):
    nome = CharField(_("nome do papel"), max_length=256)
    sigla = CharField(_("sigla"), max_length=10, blank=True, null=False, unique=True)
    papel = CharField(_("papel"), max_length=256, unique=True)
    contexto = CharField(_("contexto"), max_length=1, choices=Contexto)
    active = BooleanField(_("ativo?"))

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("papel")
        verbose_name_plural = _("papéis")
        ordering = ["nome"]

    def __str__(self):
        sigla = f"{self.sigla}:" if self.sigla else ""
        return f"{sigla}{self.nome} {self.active_icon}"


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

    def __codigo_papel(self, papel):
        return f".{papel.sigla}" if papel.sigla else ""

    @property
    def coortes(self):
        cohorts = {}

        try:

            def dados_coorte(v, campus):
                campus_curso = f"{campus.sigla}.{self.codigo}"
                id = f"{campus_curso}{self.__codigo_papel(v.papel)}"
                return {
                    "idnumber": id,
                    "nome": f"{campus_curso} - {v.papel.nome}",
                    "descricao": f"{v.papel.nome}: {campus_curso} - {self.nome}",
                    "ativo": v.active,
                    "colaboradores": [],
                    "role": v.papel.papel,
                }

            def dados_colaborador(vc):
                return {
                    "login": vc.colaborador.username,
                    "email": vc.colaborador.email,
                    "nome": vc.colaborador.get_full_name(),
                    "status": "Ativo" if vc.active else "Inativo",
                }

            for vc in self.vinculocurso_set.all():
                campus_curso = f"{vc.campus.sigla}.{self.codigo}"
                id = f"{campus_curso}{self.__codigo_papel(vc.papel)}"
                if id not in cohorts:
                    cohorts[id] = dados_coorte(vc, vc.campus)
                cohorts[id]["colaboradores"].append(dados_colaborador(vc))

            for cp in self.cursopolo_set.all():
                campus_curso = f"{cp.campus.sigla}.{self.codigo}"
                for vp in cp.polo.vinculopolo_set.all():
                    id = f"{campus_curso}{self.__codigo_papel(vp.papel)}"
                    if id not in cohorts:
                        cohorts[id] = cohorts[id] = dados_coorte(vp, cp.campus)
                    cohorts[id]["colaboradores"].append(dados_colaborador(vc))
        finally:
            return [c for c in cohorts.values()]


class VinculoCurso(ActiveMixin, Model):
    campus = ForeignKey(Campus, on_delete=PROTECT)
    curso = ForeignKey(Curso, on_delete=PROTECT)
    papel = ForeignKey(Papel, on_delete=PROTECT, limit_choices_to={"contexto": Contexto.CURSO})
    colaborador = ForeignKey(User, on_delete=PROTECT, related_name="vinculos_cursos")
    active = BooleanField(_("ativo?"))
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("vínculo no curso")
        verbose_name_plural = _("cursos x colaboradores")
        ordering = ["papel", "curso", "colaborador"]

    def __str__(self):
        return f"{self.papel}{self.curso} {self.colaborador} {self.active_icon}"


class Polo(Model):
    suap_id = CharField(_("ID do pólo no SUAP"), max_length=255, unique=True)
    nome = CharField(_("nome do pólo"), max_length=255, unique=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("pólo")
        verbose_name_plural = _("pólos")
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome}"


class CursoPolo(ActiveMixin, Model):
    curso = ForeignKey(Curso, on_delete=PROTECT)
    campus = ForeignKey(Campus, on_delete=PROTECT)
    polo = ForeignKey(Polo, on_delete=PROTECT)
    active = BooleanField(_("ativo?"))
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("pólo do curso")
        verbose_name_plural = _("pólos x cursos")
        ordering = ["curso", "polo"]

    def __str__(self):
        return f"{self.curso}:{self.polo} {self.active_icon}"


class VinculoPolo(ActiveMixin, Model):
    papel = ForeignKey(Papel, on_delete=PROTECT, limit_choices_to={"contexto": Contexto.POLO})
    polo = ForeignKey(Polo, on_delete=PROTECT)
    colaborador = ForeignKey(User, on_delete=PROTECT, related_name="vinculos_polos")
    active = BooleanField(_("ativo?"))
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("vínculo no pólo")
        verbose_name_plural = _("pólos X colaboradores")
        ordering = ["papel", "polo", "colaborador"]

    def __str__(self):
        return f"{self.papel}{self.polo} {self.colaborador} {self.active_icon}"


class SolicitacaoManager(Manager):
    def by_diario_id(self, diario_id: int) -> QuerySet:
        return Solicitacao.objects.filter(Q(recebido__diario__id=int(diario_id))).order_by("-id")

    def ultima_do_diario(self, diario_id: int) -> Model:
        return self.by_diario_id(diario_id).first()


class Solicitacao(Model):
    class Status(Choices):
        SUCESSO = Choices.Value(_("Sucesso"), value="S")
        FALHA = Choices.Value(_("Falha"), value="F")
        PROCESSANDO = Choices.Value(_("Processando"), value="P")

    timestamp = DateTimeField(_("quando ocorreu"), auto_now_add=True)
    campus = ForeignKey(Campus, on_delete=PROTECT, null=True, blank=True)
    status = CharField(_("status"), max_length=256, choices=Status, null=True, blank=True)
    status_code = CharField(_("status code"), max_length=256, null=True, blank=True)
    recebido = JSONField(_("JSON recebido"), null=True, blank=True)
    enviado = JSONField(_("JSON enviado"), null=True, blank=True)
    respondido = JSONField(_("JSON respondido"), null=True, blank=True)

    objects = SolicitacaoManager()

    class Meta:
        verbose_name = _("solicitação")
        verbose_name_plural = _("solicitações")
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.id} - {self.respondido}"

    @property
    def status_merged(self):
        return format_html(f"""{Solicitacao.Status[self.status].display}<br>{self.status_code}""")
