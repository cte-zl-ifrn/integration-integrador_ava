from django.contrib.admin.helpers import AdminForm, AdminErrorList
from django.contrib.admin.options import IS_POPUP_VAR, TO_FIELD_VAR
from django.contrib.admin.utils import flatten_fieldsets, quote, unquote
from django.core.exceptions import PermissionDenied
from django.forms.widgets import Media
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.text import capfirst
from dsgovbr.admin import DSGovBrChangeList, DSGovBrBaseModelAdmin
from import_export.admin import ExportActionMixin, ImportExportMixin


class BaseChangeList(DSGovBrChangeList):
    def url_for_result(self, result):
        return reverse(
            f"admin:{self.opts.app_label}_{self.opts.model_name}_view",
            args=(quote(getattr(result, self.pk_attname)),),
            current_app=self.model_admin.admin_site.name,
        )


class BasicModelAdmin(DSGovBrBaseModelAdmin):
    default_view = "view"

    def get_changelist(self, request, **kwargs):
        return BaseChangeList

    def get_urls(self):
        info = self.opts.app_label, self.opts.model_name
        view_url = path(
            "<path:object_id>/view/",
            self.admin_site.admin_view(self.preview_view),
            name=f"{info[0]}_{info[1]}_view",
        )

        return [view_url] + super().get_urls()

    def redirect_view(self, request, object_id, form_url="", extra_context=None):
        return redirect(
            f"admin:{self.opts.app_label}_{self.opts.model_name}_{self.default_view}",
            object_id=object_id,
        )

    def preview_view(self, request, object_id, form_url="", extra_context=None):
        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        if to_field and not self.to_field_allowed(request, to_field):
            raise PermissionDenied

        obj = self.get_object(request, unquote(object_id), to_field)

        if not self.has_view_or_change_permission(request, obj):
            raise PermissionDenied

        request.in_view_mode = True

        fieldsets = self.get_fieldsets(request, obj)
        model_form = self.get_form(
            request,
            obj,
            change=False,
            fields=flatten_fieldsets(fieldsets),
        )
        form = model_form(instance=obj)
        formsets, inline_instances = self._create_formsets(request, obj, change=True)

        readonly_fields = [*form.base_fields, *self.get_readonly_fields(request, obj)]
        admin_form = AdminForm(form, list(fieldsets), {}, readonly_fields, model_admin=self)
        media = self.media + admin_form.media

        inline_formsets = self.get_inline_formsets(request, formsets, inline_instances, obj)
        for inline_formset in inline_formsets:
            media += inline_formset.media
            inline_formset.readonly_fields = flatten_fieldsets(inline_formset.fieldsets)

        context = {
            **self.admin_site.each_context(request),
            "title": str(capfirst(self.opts.verbose_name_plural)),
            "subtitle": str(obj) if obj else None,
            "adminform": admin_form,
            "object_id": object_id,
            "original": obj,
            "obj": obj,
            "is_popup": IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET,
            "to_field": to_field,
            "media": media,
            "inline_admin_formsets": inline_formsets,
            "errors": AdminErrorList(form, formsets),
            "preserved_filters": self.get_preserved_filters(request),
            "has_delete_permission": False,
            "show_delete": False,
            "show_delete_link": False,
            "can_delete_related": False,
            "has_add_permission": False,
            "show_change": False,
            "can_change_related": False,
            "show_save": False,
            "show_save_as_new": False,
            "show_save_and_add_another": False,
            "show_save_and_continue": False,
            "show_change_form_export": True,
            "can_view_related": True,
        }
        context.update(extra_context or {})

        return self.render_change_form(
            request,
            context,
            add=False,
            change=False,
            obj=obj,
            form_url=form_url,
        )

    @property
    def media(self):
        parent_media = super().media if hasattr(super(), "media") else Media()
        return parent_media


class BaseModelAdmin(ImportExportMixin, ExportActionMixin, BasicModelAdmin):
    pass
