from django.utils.translation import gettext as _
from django.db.models import CharField, DateTimeField, JSONField, BooleanField, ForeignKey, PROTECT
from django.db.models import Manager, Model, QuerySet, Q
from django_better_choices import Choices
from simple_history.models import HistoricalRecords
from django.utils.html import format_html
from base.models import ActiveMixin


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
    def moodle_base_api_url(self):
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


class Solicitacao(Model):
    class Status(Choices):
        NAO_DEFINIDO = Choices.Value(_("Não Definido"), value=None)
        SUCESSO = Choices.Value(_("Sucesso"), value="S")
        FALHA = Choices.Value(_("Falha"), value="F")
        PROCESSANDO = Choices.Value(_("Processando"), value="P")

    class SolicitacaoManager(Manager):
        def by_diario_id(self, diario_id: int) -> QuerySet:
            return Solicitacao.objects.filter(Q(recebido__diario__id=int(diario_id))).order_by("-id")

        def ultima_do_diario(self, diario_id: int) -> Model:
            return self.by_diario_id(diario_id).first()

    timestamp = DateTimeField(_("quando ocorreu"), auto_now_add=True)
    campus = ForeignKey(Campus, on_delete=PROTECT, null=True, blank=True)
    status = CharField(_("status"), max_length=256, choices=Status, null=True, blank=False)
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
