from django.utils.translation import gettext as _
import json
from django.db.models import CharField, DateTimeField, JSONField, BooleanField, IntegerField, TextField
from django.db.models import ForeignKey, PROTECT
from django.db.models import Manager, Model
from django.utils.html import format_html
from django_better_choices import Choices
from sga.db.fields import PermissiveURLField
from rule_engine import Rule


class Ambiente(Model):
    class AmbienteManager(Manager):
        def seleciona_ambiente(self, sync_json: dict) -> Model:
            ambientes = Ambiente.objects.filter(active=True)
            for a in ambientes:
                try:
                    if Rule(a.expressao_seletora).matches(sync_json):
                        return a
                except Exception as e:
                    raise Exception(f"Erro ao processar o ambiente {a} ({a.expressao_seletora}): {e} {sync_json}")
            return None

    def _c(color: str):
        return f"""<span style='background: {color}; color: #fff; padding: 1px 5px; font-size: 95%; border-radius: 4px;'>{color}</span>"""

    nome = CharField(_("nome do ambiente"), max_length=255)
    url = PermissiveURLField(_("URL"), max_length=255)
    expressao_seletora = TextField(_("expressão seletora"), max_length=2550, null=True, blank=True)
    ordem = IntegerField(_("ordem"), default=0)
    local_suap_token = CharField(_("token local_suap"), max_length=255, null=True, blank=True)
    local_suap_active = BooleanField(_("local_suap ativo?"), default=True)
    tool_sga_token = CharField(_("token tool_sga"), max_length=255, null=True, blank=True)
    tool_sga_active = BooleanField(_("tool_sga ativo?"), default=True)

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
    def valid_expressao_seletora(self):
        try:
            if self.expressao_seletora is None or self.expressao_seletora.strip() == "":
                return False
            Rule(self.expressao_seletora)
            return True
        except Exception:
            return False


class Solicitacao(Model):
    class Status(Choices):
        NAO_DEFINIDO = Choices.Value(_("Não Definido"), value=None)
        SUCESSO = Choices.Value(_("Sucesso"), value="S")
        FALHA = Choices.Value(_("Falha"), value="F")
        PROCESSANDO = Choices.Value(_("Processando"), value="P")

    class Operacao(Choices):
        SYNC_UP_DIARIO = Choices.Value(
            _("Sync UP: Diário"), value="SUDiario", schema=json.load(open("integrador/static/SUDiario.schema.json"))
        )
        SYNC_DOWN_NOTAS = Choices.Value(
            _("Sync DOWN: Notas"), value="SDNotas", schema=json.load(open("integrador/static/SDNotas.schema.json"))
        )

    ambiente = ForeignKey(Ambiente, verbose_name=_("ambiente"), on_delete=PROTECT, null=True, blank=False)
    timestamp = DateTimeField(_("quando ocorreu"), auto_now_add=True, db_index=True)
    campus_sigla = CharField(_("campus"), max_length=256, null=True, blank=True)
    diario_codigo = CharField(_("código do diário"), max_length=256, null=True, blank=True)
    diario_id = CharField(_("ID do diário"), max_length=256, null=True, blank=True)
    operacao = CharField(
        _("operação"),
        max_length=256,
        choices=Operacao.choices,
        null=False,
        blank=False,
        default=Operacao.SYNC_UP_DIARIO,
    )
    tipo = CharField(_("tipo de diário"), max_length=256, null=True, blank=True, default=None)
    status = CharField(_("status"), max_length=256, choices=Status.choices, null=True, blank=False)
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
        return format_html("{}<br>{}", self.get_status_display(), self.status_code or "")

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.recebido:
            diario = self.recebido.get("diario", {})
            componente = diario.get("sigla", "")
            turma = self.recebido.get("turma", {}).get("codigo", "")

            self.ambiente = Ambiente.objects.seleciona_ambiente(self.recebido)
            self.campus_sigla = self.recebido.get("campus", {}).get("sigla", None)
            self.diario_id = diario.get("id", "")
            self.diario_codigo = f"{turma}.{componente}#{self.diario_id}"
            self.tipo = self.recebido.get("diario", {}).get(
                "tipo", "regular" if self.operacao == Solicitacao.Operacao.SYNC_UP_DIARIO else None
            )
        return super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
