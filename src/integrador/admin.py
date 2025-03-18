from django.utils.translation import gettext as _
from functools import update_wrapper
from django.utils.safestring import mark_safe
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.db import transaction
from django.urls import path, reverse
from django.db.models import JSONField, Model
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.contrib.admin import (
    register,
    display,
    StackedInline,
    TabularInline,
    ModelAdmin,
)
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.utils import quote, unquote
from django.contrib.admin.options import IS_POPUP_VAR, TO_FIELD_VAR, flatten_fieldsets
from django.contrib.admin.helpers import AdminErrorList, AdminForm, InlineAdminFormSet
from django.contrib.admin.exceptions import DisallowedModelAdminToField
from django.core.exceptions import PermissionDenied
from django_json_widget.widgets import JSONEditorWidget
from import_export.admin import ImportExportMixin, ExportActionMixin
from import_export.resources import ModelResource
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget, DateTimeWidget
from integrador.models import (
    Ambiente,
    Campus,
    Papel,
    Curso,
    Polo,
    CursoPolo,
    VinculoCurso,
    VinculoPolo,
    Programa,
    CursoPrograma,
    VinculoPrograma,
    Solicitacao,
)
from integrador.brokers import MoodleBroker


DEFAULT_DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"
DEFAULT_DATETIME_FORMAT_WIDGET = DateTimeWidget(format=DEFAULT_DATETIME_FORMAT)


####
# Base classes
####


class BaseChangeList(ChangeList):
    def url_for_result(self, result):
        pk = getattr(result, self.pk_attname)
        return reverse(
            "admin:%s_%s_view" % (self.opts.app_label, self.opts.model_name),
            args=(quote(pk),),
            current_app=self.model_admin.admin_site.name,
        )


class BaseModelAdmin(ImportExportMixin, ExportActionMixin, ModelAdmin):
    list_filter = []

    def get_changelist(self, request, **kwargs):
        return BaseChangeList

    def get_urls(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        prefix = f"{self.opts.app_label}_{self.opts.model_name}"
        urls = [url for url in super().get_urls() if url.pattern.name is not None]
        urls.append(path("<path:object_id>/", wrap(self.preview_view), name=f"{prefix}_view"))
        return urls

    def preview_view(self, request, object_id, form_url="", extra_context=None):
        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        if to_field and not self.to_field_allowed(request, to_field):
            raise DisallowedModelAdminToField(f"The field {to_field} cannot be referenced.")

        obj = self.get_object(request, unquote(object_id), to_field)

        if not self.has_view_or_change_permission(request, obj):
            raise PermissionDenied

        request.in_view_mode = True

        fieldsets = self.get_fieldsets(request, obj)
        ModelForm = self.get_form(request, obj, change=False, fields=flatten_fieldsets(fieldsets))
        form = ModelForm(instance=obj)
        formsets, inline_instances = self._create_formsets(request, obj, change=True)

        # form = self._get_form_for_get_fields(request, obj)
        # return [*form.base_fields, *self.get_readonly_fields(request, obj)]
        readonly_fields = [*form.base_fields, *self.get_readonly_fields(request, obj)]
        admin_form = AdminForm(form, list(fieldsets), {}, readonly_fields, model_admin=self)
        media = self.media + admin_form.media

        inline_formsets = self.get_inline_formsets(request, formsets, inline_instances, obj)
        # inline_formsets = []
        for inline_formset in inline_formsets:
            media += inline_formset.media
            inline_formset.readonly_fields = flatten_fieldsets(inline_formset.fieldsets)

        context = {
            **self.admin_site.each_context(request),
            "title": _("View %s") % self.opts.verbose_name,
            "subtitle": str(obj) if obj else None,
            "adminform": admin_form,
            "object_id": object_id,
            "original": obj,
            "is_popup": IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET,
            "to_field": to_field,
            "media": media,
            "inline_admin_formsets": inline_formsets,
            "errors": AdminErrorList(form, formsets),
            "preserved_filters": self.get_preserved_filters(request),
            "has_add_permission": True,
            "has_delete_permission": True,
            "show_delete": True,
            "change": False,
        }

        context.update(extra_context or {})

        return self.render_change_form(request, context, add=False, change=False, obj=obj, form_url=form_url)

    def get_inline_formsets(self, request, formsets, inline_instances, obj=None):
        # Edit permissions on parent model are required for editable inlines.
        if getattr(request, "in_view_mode", False):
            can_edit_parent = False
        else:
            can_edit_parent = self.has_change_permission(request, obj) if obj else self.has_add_permission(request)

        inline_admin_formsets = []
        for inline, formset in zip(inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request, obj))
            readonly = list(inline.get_readonly_fields(request, obj))
            if can_edit_parent:
                has_add_permission = inline.has_add_permission(request, obj)
                has_change_permission = inline.has_change_permission(request, obj)
                has_delete_permission = inline.has_delete_permission(request, obj)
            else:
                # Disable all edit-permissions, and override formset settings.
                has_add_permission = has_change_permission = has_delete_permission = False
                formset.extra = formset.max_num = 0
            has_view_permission = inline.has_view_permission(request, obj)
            prepopulated = dict(inline.get_prepopulated_fields(request, obj))
            inline_admin_formset = InlineAdminFormSet(
                inline,
                formset,
                fieldsets,
                prepopulated,
                readonly,
                model_admin=self,
                has_add_permission=has_add_permission,
                has_change_permission=has_change_permission,
                has_delete_permission=has_delete_permission,
                has_view_permission=has_view_permission,
            )
            inline_admin_formsets.append(inline_admin_formset)
        return inline_admin_formsets


####
# Inlines
####


class CampusInline(StackedInline):
    model: Model = Campus
    extra: int = 0


class VinculoCursoInline(TabularInline):
    model: Model = VinculoCurso
    extra: int = 0


class VinculoPoloInline(TabularInline):
    model: Model = VinculoPolo
    extra: int = 0


class CursoPoloInline(TabularInline):
    model: Model = CursoPolo
    extra: int = 0


class VinculoProgramaInline(TabularInline):
    model: Model = VinculoPrograma
    extra: int = 0


class CursoProgramaInline(TabularInline):
    model: Model = CursoPrograma
    extra: int = 0


####
# Admins
####


@register(Ambiente)
class AmbienteAdmin(BaseModelAdmin):
    class CampusInline(StackedInline):
        model = Campus
        extra = 0

    class AmbienteResource(ModelResource):
        class Meta:
            model = Ambiente
            export_order = ("nome", "url", "token", "active")
            import_id_fields = ("nome",)
            fields = export_order
            skip_unchanged = True

    list_display = ["nome", "url", "active"]
    history_list_display = list_display
    field_to_highlight = list_display[0]
    search_fields = ["nome", "url"]
    list_filter = ["active"]
    fieldsets = [
        (_("Identificação"), {"fields": ["nome"]}),
        (_("Integração"), {"fields": ["active", "url", "token"]}),
    ]
    inlines = [CampusInline]
    resource_classes = [AmbienteResource]


@register(Campus)
class CampusAdmin(BaseModelAdmin):
    class CampusResource(ModelResource):
        ambiente = Field(
            attribute="ambiente",
            column_name="nome_ambiente",
            widget=ForeignKeyWidget(Ambiente, field="nome"),
        )

        class Meta:
            model = Campus
            export_order = ("sigla", "ambiente", "suap_id", "active")
            import_id_fields = ("sigla",)
            fields = export_order
            skip_unchanged = True

    list_display = ["sigla", "ambiente", "active"]
    history_list_display = list_display
    field_to_highlight = list_display[0]
    list_filter = ["active", "ambiente"]
    search_fields = ["sigla", "suap_id"]
    resource_classes = [CampusResource]


@register(Curso)
class CursoAdmin(BaseModelAdmin):
    class CursoResource(ModelResource):
        class Meta:
            model = Curso
            export_order = ("codigo", "nome", "suap_id")
            import_id_fields = ("codigo",)
            fields = export_order
            skip_unchanged = True

    list_display = ["codigo", "nome"]
    history_list_display = list_display
    field_to_highlight = list_display[0]
    search_fields = ["codigo", "nome", "suap_id"]
    resource_classes = [CursoResource]
    inlines = [CursoPoloInline, VinculoCursoInline, CursoProgramaInline]


@register(Polo)
class PoloAdmin(BaseModelAdmin):
    class PoloResource(ModelResource):
        class Meta:
            model = Polo
            export_order = ["suap_id", "nome"]
            import_id_fields = ("suap_id",)
            fields = export_order
            skip_unchanged = True

    list_display = ["nome"]
    search_fields = ["nome", "suap_id"]
    resource_classes = [PoloResource]
    inlines = [VinculoPoloInline]


@register(Papel)
class PapelAdmin(BaseModelAdmin):
    class PapelResource(ModelResource):
        class Meta:
            model = Papel
            export_order = ["papel", "sigla", "nome", "contexto", "active"]
            import_id_fields = ("papel",)
            fields = export_order
            skip_unchanged = True

    list_display = ["nome", "sigla", "contexto", "active"]
    list_filter = ["active", "contexto"] + BaseModelAdmin.list_filter
    search_fields = ["nome", "sigla", "contexto"]
    resource_classes = [PapelResource]


@register(VinculoCurso)
class VinculoCursoAdmin(BaseModelAdmin):
    class VinculoCursoResource(ModelResource):
        colaborador = Field(
            attribute="colaborador",
            column_name="colaborador",
            widget=ForeignKeyWidget(User, field="username"),
        )
        curso = Field(
            attribute="curso",
            column_name="curso",
            widget=ForeignKeyWidget(Curso, field="codigo"),
        )
        papel = Field(
            attribute="papel",
            column_name="papel",
            widget=ForeignKeyWidget(Papel, field="papel"),
        )
        campus = Field(
            attribute="campus",
            column_name="campus",
            widget=ForeignKeyWidget(Campus, field="sigla"),
        )

        class Meta:
            model = VinculoCurso
            export_order = ["colaborador", "curso", "papel", "campus", "active"]
            import_id_fields = ("colaborador", "curso", "papel", "campus")
            fields = export_order
            skip_unchanged = True

    list_display = ["papel", "curso", "colaborador", "active"]
    list_filter = ["active", "papel"] + BaseModelAdmin.list_filter
    search_fields = ["colaborador__nome_social", "colaborador__nome_civil"]
    autocomplete_fields = ["curso", "colaborador"]
    resource_classes = [VinculoCursoResource]


@register(VinculoPolo)
class VinculoPoloAdmin(BaseModelAdmin):
    class VinculoPoloResource(ModelResource):
        colaborador = Field(
            attribute="colaborador",
            column_name="colaborador",
            widget=ForeignKeyWidget(User, field="username"),
        )
        polo = Field(
            attribute="polo",
            column_name="polo",
            widget=ForeignKeyWidget(Polo, field="suap_id"),
        )
        papel = Field(
            attribute="papel",
            column_name="papel",
            widget=ForeignKeyWidget(Papel, field="papel"),
        )

        class Meta:
            model = VinculoPolo
            export_order = ["papel", "polo", "colaborador", "active"]
            import_id_fields = ("papel", "polo", "colaborador")
            fields = export_order
            skip_unchanged = True

    list_display = ["papel", "polo", "colaborador", "active"]
    list_filter = ["active", "papel", "papel"] + BaseModelAdmin.list_filter
    search_fields = ["colaborador__nome_social", "colaborador__nome_civil"]
    autocomplete_fields = ["polo", "colaborador"]
    resource_classes = [VinculoPoloResource]


@register(Programa)
class ProgramaAdmin(BaseModelAdmin):
    class ProgramaResource(ModelResource):
        class Meta:
            model = Programa
            export_order = ["suap_id", "nome", "sigla"]
            import_id_fields = ("suap_id",)
            fields = export_order
            skip_unchanged = True

    list_display = ["nome", "sigla"]
    search_fields = ["nome", "suap_id", "sigla"]
    resource_classes = [ProgramaResource]
    inlines = [VinculoProgramaInline]


@register(VinculoPrograma)
class VinculoProgramaAdmin(BaseModelAdmin):
    class VinculoProgramaResource(ModelResource):
        colaborador = Field(
            attribute="colaborador",
            column_name="colaborador",
            widget=ForeignKeyWidget(User, field="username"),
        )
        programa = Field(
            attribute="programa",
            column_name="programa",
            widget=ForeignKeyWidget(Programa, field="suap_id"),
        )
        papel = Field(
            attribute="papel",
            column_name="papel",
            widget=ForeignKeyWidget(Papel, field="papel"),
        )

        class Meta:
            model = VinculoPrograma
            export_order = ["papel", "programa", "colaborador", "active"]
            import_id_fields = ("papel", "programa", "colaborador")
            fields = export_order
            skip_unchanged = True

    list_display = ["papel", "programa", "colaborador", "active"]
    list_filter = ["active", "papel", "papel"] + BaseModelAdmin.list_filter
    search_fields = ["colaborador__nome_social", "colaborador__nome_civil"]
    autocomplete_fields = ["programa", "colaborador"]
    resource_classes = [VinculoProgramaResource]


@register(CursoPrograma)
class CursoProgramaAdmin(BaseModelAdmin):
    class CursoProgramaResource(ModelResource):
        curso = Field(
            attribute="curso",
            column_name="curso",
            widget=ForeignKeyWidget(Curso, field="codigo"),
        )
        programa = Field(
            attribute="programa",
            column_name="programa",
            widget=ForeignKeyWidget(Polo, field="suap_id"),
        )

        class Meta:
            model = CursoPrograma
            export_order = ["curso", "programa", "active"]
            import_id_fields = ("curso", "programa")
            fields = export_order
            skip_unchanged = True
    list_display = ["curso", "programa", "active"]
    autocomplete_fields = ["curso", "programa"]

@register(CursoPolo)
class CursoPoloResourceAdmin(BaseModelAdmin):
    class CursoPoloResource(ModelResource):
        curso = Field(
            attribute="curso",
            column_name="curso",
            widget=ForeignKeyWidget(Curso, field="codigo"),
        )
        polo = Field(
            attribute="polo",
            column_name="polo",
            widget=ForeignKeyWidget(Polo, field="suap_id"),
        )
        campus = Field(
            attribute="campus",
            column_name="campus",
            widget=ForeignKeyWidget(Campus, field="sigla"),
        )

        class Meta:
            model = CursoPolo
            export_order = ["curso", "polo", "active"]
            import_id_fields = ("curso", "polo")
            fields = export_order
            skip_unchanged = True

    list_display = ["curso", "polo", "active"]
    list_filter = ["active"] + BaseModelAdmin.list_filter
    autocomplete_fields = ["curso", "polo"]
    resource_classes = [CursoPoloResource]


@register(Solicitacao)
class SolicitacaoAdmin(BaseModelAdmin):
    list_display = (
        "quando",
        "status_merged",
        "campus",
        "codigo_diario",
        "professores",
        "acoes",
    )
    list_filter = ("status", "status_code", "campus__sigla")
    search_fields = ["recebido", "enviado", "respondido", "diario__codigo"]
    autocomplete_fields = ["campus"]
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
            return format_html(
                "<ul>" + "".join([f"<li>{x['nome']}</li>" for x in obj.recebido["professores"]]) + "</ul>"
            )
        except Exception:
            return "-"

    @display(description="Diário", ordering="timestamp")
    def codigo_diario(self, obj):
        try:
            codigo = (
                f"{obj.recebido['turma']['codigo']}.{obj.recebido['diario']['sigla']}#{obj.recebido['diario']['id']}"
            )
            try:
                suap_url = "https://suap.ifrn.edu.br"
                return format_html(
                    f"""<ul><li><a href='{obj.respondido['url']}'>{codigo}</a></li>
                        <li><a href='{obj.respondido['url_sala_coordenacao']}'>Sala de coordenação</a></li>
                        <li><a href='{suap_url}/edu/meu_diario/{obj.recebido['diario']['id']}/1/'>Diário no SUAP</a></li></ul>"""
                )
            except Exception:
                return codigo
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
