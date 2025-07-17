from django.utils.translation import gettext as _
import json
from django.db.models import CharField, DateTimeField, JSONField, BooleanField, IntegerField, TextField, ForeignKey, PROTECT
from django.db.models import Manager, Model, QuerySet, Q
from django.utils.html import format_html
from django_better_choices import Choices
from simple_history.models import HistoricalRecords
from rule_engine import Rule
from base.models import ActiveMixin


class Ambiente(Model):
    class AmbienteManager(Manager):
        def seleciona_ambiente(self, sync_json: dict) -> Model:
            ambientes = Ambiente.objects.filter(active=True)
            for a in ambientes:
                try:
                    if Rule(a.expressao_seletora).matches(sync_json):
                        return a
                except Exception as e:
                    raise Exception(f"Erro ao processar o ambiente {a}: {e}")
            return None

    def _c(color: str):
        return f"""<span style='background: {color}; color: #fff; padding: 1px 5px; font-size: 95%; border-radius: 4px;'>{color}</span>"""

    nome = CharField(_("nome do ambiente"), max_length=255)
    url = CharField(_("URL"), max_length=255)
    token = CharField(_("token"), max_length=255)
    expressao_seletora = TextField(_("expressão seletora"), max_length=2550)
    ordem = IntegerField(_("ordem"), default=0)
    active = BooleanField(_("ativo?"), default=True)

    objects = AmbienteManager()

    class Meta:
        verbose_name = _("ambiente")
        verbose_name_plural = _("ambientes")
        ordering = ["ordem", "id"]

    def __str__(self):
        return f"{self.nome}"

    @property
    def base_url(self):
        return self.url if self.url[-1:] != "/" else self.url[:-1]

    @property
    def moodle_base_api_url(self):
        return f"{self.base_url}/local/suap/api"

    @property
    def credentials(self):
        return {"Authentication": f"Token {self.token}"}


class Solicitacao(Model):
    class Status(Choices):
        NAO_DEFINIDO = Choices.Value(_("Não Definido"), value=None)
        SUCESSO = Choices.Value(_("Sucesso"), value="S")
        FALHA = Choices.Value(_("Falha"), value="F")
        PROCESSANDO = Choices.Value(_("Processando"), value="P")

    class Operacao(Choices):
        SYNC_UP_DIARIO = Choices.Value(_("Sync UP: Diário"), value="SUDiario", schema=json.load(open(f"integrador/static/SUDiario.schema.json")))
        SYNC_DOWN_NOTAS = Choices.Value(_("Sync DOWN: Notas"), value="SDNotas", schema=json.load(open(f"integrador/static/SDNotas.schema.json")))

    class Tipo(Choices):
        DIARIO = Choices.Value(_("Diário"), value="diario")
        FICMENOS = Choices.Value(_("FIC-"), value="fic-")
        MINICURSO = Choices.Value(_("Minicurso"), value="minicurso")

    ambiente = ForeignKey(Ambiente, verbose_name=_("ambiente"), on_delete=PROTECT, null=True, blank=False)
    timestamp = DateTimeField(_("quando ocorreu"), auto_now_add=True, db_index=True)
    campus_sigla = CharField(_("sigla do campus"), max_length=256, null=True, blank=True)
    diario_codigo = CharField(_("código do diário"), max_length=256, null=True, blank=True)
    diario_id = CharField(_("ID do diário"), max_length=256, null=True, blank=True)
    operacao = CharField(_("operação"), max_length=256, choices=Operacao, null=False, blank=False, default=Operacao.SYNC_UP_DIARIO)
    tipo = CharField(_("tipo"), max_length=256, choices=Tipo, null=False, blank=False, default=Tipo.DIARIO)
    status = CharField(_("status"), max_length=256, choices=Status, null=True, blank=False)
    status_code = CharField(_("status code"), max_length=256, null=True, blank=True)
    recebido = JSONField(_("JSON recebido"), null=True, blank=True)
    enviado = JSONField(_("JSON enviado"), null=True, blank=True)
    respondido = JSONField(_("JSON respondido"), null=True, blank=True)

    class Meta:
        verbose_name = _("solicitação")
        verbose_name_plural = _("solicitações")
        
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.id}={self.status}, {self.tipo}[{self.ambiente}]: {self.campus_sigla}-{self.diario_id}"

    @property
    def status_merged(self):
        return format_html(f"""{Solicitacao.Status[self.status].display}<br>{self.status_code}""")

