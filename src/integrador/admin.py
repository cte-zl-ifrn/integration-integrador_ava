from django.utils.translation import gettext as _
import requests
from functools import update_wrapper
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.html import format_html
from django.db import transaction
from django.urls import path, reverse
from django.db.models import JSONField
from django.forms import ModelForm
from django.contrib.admin import register, display
from django_json_widget.widgets import JSONEditorWidget
from import_export.resources import ModelResource
from base.admin import BaseModelAdmin
from integrador.models import Ambiente, Solicitacao
from integrador.brokers import MoodleBroker


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
        (_("Integração"), {"fields": ["active", "url", "token", "expressao_seletora", "ordem"]}),
    ]
    resource_classes = [AmbienteResource]

    @display(description="URL")
    def checked_url(self, obj):
        try:
            response = requests.get(f'{obj.url}/version.php', timeout=1)
            if response.status_code == 200:
                return format_html(f'<a href="{obj.url}">{obj.url}</a> ✅')
            else:
                return format_html(f'<a href="{obj.url}">{obj.url}</a> 🚫 ({response.status_code})')
        except Exception:
            return format_html(f'<a href="{obj.url}">{obj.url}</a> 🚫')

    @display(description="URL")
    def checked_expressao_seletora(self, obj):
        if obj.expressao_seletora is None or obj.expressao_seletora.strip() == "":
            return format_html('<span style="color: orange;">Não configurada ⚠️</span>')
        elif obj.valid_expressao_seletora:
            return format_html(f'<code>{obj.expressao_seletora}</code> ✅')
        else:
            return format_html(f'<span style="color: red;">{obj.expressao_seletora} (É inválida 🚫)</span>')



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
        return format_html(f"""{Solicitacao.Status[obj.status].display}<br>{obj.status_code}""")

    @display(description="Ações")
    def acoes(self, obj):
        return format_html(
            f"""<a class="export_link" href="{reverse("admin:integrador_solicitacao_sync", args=[obj.id])}">Reenviar</a>"""
        )

    @display(description="Quando", ordering="timestamp")
    def quando(self, obj):
        return obj.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    @display(description="Professores", ordering="timestamp")
    def professores(self, obj):
        try:
            profs = ""
            for p in (obj.recebido or {}).get("professores", []):
                username = p.get('login', None)
                urlpath = '/admin/comum/prestadorservico/?q=' if username and len(username) > 10 else '/admin/rh/servidor/?ativo__exact=1&q='
                vinculo = 'externo' if username and len(username) > 10 else 'servidor'
                profs += f'<li><a href="{settings.SUAP_BASE_URL}{urlpath}{username}">{p.get("nome")} ({p.get("tipo")}:{vinculo})</a></li>'
            return format_html(f"<ul>{profs}</ul>")
        except Exception:
            return "-"

    @display(description="Links", ordering="timestamp")
    def codigo_diario(self, obj):
        respondido = obj.respondido or {}
        try:
            return format_html(
                f"""<ul><li><a href='{respondido.get('url', '#')}'>{obj.diario_codigo}</a></li>
                    <li><a href='{respondido.get('url_sala_coordenacao', '#')}'>Sala de coordenação</a></li>
                    <li><a href='{settings.SUAP_BASE_URL}/edu/meu_diario/{obj.diario_id}/1/'>Diário no SUAP</a></li></ul>"""
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
            solicitacao = MoodleBroker().sync(s.recebido)
            if solicitacao is None:
                raise Exception("Erro desconhecido.")
            return HttpResponseRedirect(reverse("admin:integrador_solicitacao_view", args=[solicitacao.id]))
        except Exception as e:
            return HttpResponse(f"{e}")

