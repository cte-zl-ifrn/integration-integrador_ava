from django.utils.translation import gettext as _
import logging
import requests
from functools import update_wrapper
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime
from django.db import transaction
from django.urls import path, reverse
from django.db.models import JSONField
from django.forms import ModelForm
from django.contrib.admin import register, display
from django_json_widget.widgets import JSONEditorWidget
from import_export.resources import ModelResource
from base.admin import BaseModelAdmin
from integrador.models import Ambiente, Solicitacao
from integrador.brokers.suap2local_suap import Suap2LocalSuapBroker

logger = logging.getLogger(__name__)


####
# Admins
####
@register(Ambiente)
class AmbienteAdmin(BaseModelAdmin):
    class AmbienteResource(ModelResource):
        class Meta:
            model = Ambiente
            export_order = ("nome", "url", "token", "active")
            import_id_fields = ("nome",)
            fields = export_order
            skip_unchanged = True

    list_display = ["nome", "checked_url", "checked_expressao_seletora", "active"]
    history_list_display = list_display
    field_to_highlight = list_display[0]
    search_fields = ["nome", "url"]
    list_filter = ["active"]
    fieldsets = [
        (_("Identificação"), {"fields": ["nome"]}),
        (_("    "), {"fields": ["active", "url", "token", "expressao_seletora", "ordem"]}),
    ]
    resource_classes = [AmbienteResource]

    def get_queryset(self, request):
        """Otimiza queryset para evitar N+1 queries."""
        return super().get_queryset(request).all()

    @display(description="URL")
    def checked_url(self, obj):
        validation_error = '<span title="Erro ao tentar validar a URL deste AVA."> 🚫</span>'
        validation_success = '<span title="A URL deste AVA foi validada com sucesso."> ✅</span>'
        try:
            response = requests.get(f"{obj.url}/version.php", timeout=1)
            message = validation_success if response.status_code == 200 else validation_error
        except Exception:
            message = validation_error
        return format_html('{message}<a href="{url}">{url}🔗</a>', url=obj.url, message=mark_safe(message))

    @display(description="Expressão Seletora")
    def checked_expressao_seletora(self, obj):
        if obj.expressao_seletora is None or obj.expressao_seletora.strip() == "":
            title = "Não configurada"
            status = "⚠️"
            color = "orange"
        elif obj.valid_expressao_seletora:
            title = "Regra validada com sucesso."
            status = "✅"
            color = "green"
        else:
            title = "Regra inválida."
            status = "🚫"
            color = "red"

        es = obj.expressao_seletora or ""
        return format_html(
            '<span title="{title}"> {status}</span><span style="color: {color};">{expressao_seletora}</span>',
            expressao_seletora=(es if es.strip() != "" else f""),
            title=title,
            status=status,
            color=color,
        )


@register(Solicitacao)
class SolicitacaoAdmin(BaseModelAdmin):
    list_display = (
        "quando",
        "operacao",
        "tipo",
        "status_merged",
        "ambiente",
        "campus_sigla",
        "codigo_diario",
        "professores",
        "acoes",
    )
    list_filter = ("operacao", "tipo", "ambiente", "status", "status_code", "campus_sigla")

    search_fields = ["diario_codigo", "diario_id"]
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)

    def get_queryset(self, request):
        """Otimiza queryset para evitar N+1 queries ao acessar ForeignKey 'ambiente'."""
        return super().get_queryset(request).select_related("ambiente")

    class SolicitacaoAdminForm(ModelForm):
        class Meta:
            model = Solicitacao
            widgets = {
                "recebido": JSONEditorWidget(),
                "enviado": JSONEditorWidget(),
                "respondido": JSONEditorWidget(),
            }
            fields = "__all__"
            readonly_fields = ["timestamp"]

    formfield_overrides = {JSONField: {"widget": JSONEditorWidget}}
    form = SolicitacaoAdminForm

    @display(description="Status")
    def status_merged(self, obj):
        return format_html("{}<br>{}", obj.get_status_display(), obj.status_code or "")

    @display(description="Ações")
    def acoes(self, obj):
        return format_html(
            '<a class="export_link" href="{}">Reenviar</a>',
            reverse("admin:integrador_solicitacao_sync", args=[obj.id]),
        )

    @display(description="Quando", ordering="timestamp")
    def quando(self, obj):
        if obj.timestamp:
            local = localtime(obj.timestamp)
            return local.strftime("%d/%m/%Y %H:%M:%S")
        return "-"

    @display(description="Professores", ordering="timestamp")
    def professores(self, obj):
        try:
            professores = []
            for p in (obj.recebido or {}).get("professores", []):
                username = p.get("login", None)
                urlpath = (
                    "/admin/comum/prestadorservico/?q="
                    if username and len(username) > 10
                    else "/admin/rh/servidor/?ativo__exact=1&q="
                )
                vinculo = "externo" if username and len(username) > 10 else "servidor"
                professores.append(
                    format_html(
                        '<li><a href="{}{}{}">{} ({}:{})</a></li>',
                        settings.SUAP_BASE_URL,
                        urlpath,
                        username or "",
                        p.get("nome", "-"),
                        p.get("tipo", "-"),
                        vinculo,
                    ),
                )

            if not professores:
                return "-"

            return format_html("<ul>{}</ul>", mark_safe("".join(professores)))
        except Exception:
            return "-"

    @display(description="Links", ordering="timestamp")
    def codigo_diario(self, obj):
        respondido = obj.respondido or {}
        try:
            return format_html(
                "<ul>"
                '<li><a href="{}">{}</a></li>'
                '<li><a href="{}">Sala de coordenação</a></li>'
                '<li><a href="{}/edu/meu_diario/{}/1/">Diário no SUAP</a></li>'
                "</ul>",
                respondido.get("url", "#"),
                obj.diario_codigo or "-",
                respondido.get("url_sala_coordenacao", "#"),
                settings.SUAP_BASE_URL,
                obj.diario_id or "-",
            )
        except Exception:
            return "-"

    def get_urls(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            path(
                "<path:object_id>/sync_moodle/",
                wrap(self.sync_moodle_view),
                name="%s_%s_sync" % info,
            )
        ] + super().get_urls()

    @transaction.atomic
    def sync_moodle_view(self, request, object_id, form_url="", extra_context=None):
        s = get_object_or_404(Solicitacao, pk=object_id)
        try:
            solicitacao = Suap2LocalSuapBroker(s).sync_up_enrolments()
            if solicitacao is None:
                raise Exception("Erro desconhecido.")
            return HttpResponseRedirect(reverse("admin:integrador_solicitacao_change", args=[solicitacao.id]))
        except Exception as e:
            logger.exception(f"Error while syncing Moodle for Solicitacao {s.id}. ERROR: {e}")
            return HttpResponse(
                _("An internal error has occurred while syncing. Please contact the administrator.") + f" {e}"
            )
