from django.utils.translation import gettext as _
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.contrib.admin import register, display, StackedInline, ModelAdmin, site
from django.utils.html import format_html
from django.contrib.auth.models import User
from import_export.resources import ModelResource
from base.admin import BaseModelAdmin


site.unregister(User)


@register(User)
class UserAdmin(BaseModelAdmin):
    class UserResource(ModelResource):
        class Meta:
            model = User
            export_order = [
                "username",
                "first_name",
                "last_name",
                "email",
                "active",
                "is_superuser",
                "is_active",
                "is_staff",
            ]
            import_id_fields = ("username",)
            fields = export_order
            skip_unchanged = True

    list_display = ["username", "first_name", "last_name", "email", "auth"]
    list_filter = ["is_superuser", "is_active", "is_staff"]
    search_fields = ["first_name", "last_name", "username", "email"]
    fieldsets = [
        (
            _("Identificação"),
            {
                "fields": ["username", "first_name", "last_name", "email"],
                "description": _("Identifica o usuário."),
            },
        ),
        (
            _("Autorização e autenticação"),
            {
                "fields": [("is_active", "is_staff", "is_superuser")],
                "description": _(
                    "Controla a identidade do usuário nos sistemas, qual seu papel e quais suas autorizações."
                ),
            },
        ),
        (
            _("Dates"),
            {
                "fields": [("date_joined", "last_login")],
                "description": _("Eventos relevantes relativos a este usuário"),
            },
        ),
        (
            _("Permissions"),
            {
                "fields": [("groups")],
                "description": _("Permissões e grupos aos quais o usuário pertence."),
            },
        ),
    ]
    readonly_fields = ["date_joined", "last_login"]
    # autocomplete_fields: Sequence[str] = ['groups']
    resource_classes = [UserResource]

    @display
    def auth(self, obj):
        result = "<span title='Ativo'>✅</span>" if obj.is_active else "<span title='Inativo'>❌</span>"
        if obj.is_staff and obj.is_superuser:
            result += "<span title='Super usuário'>👮‍♂️</span>"
        elif obj.is_superuser and not obj.is_staff:
            result += "<span title='Super usuário sem permissão de operar o admin? Você configurou certo?'>🕵️‍♂️</span>"
        elif obj.is_staff and not obj.is_superuser:
            result += "<span title='Pode operar o admin'>👷‍♂️</span>"
        elif not obj.is_staff and not obj.is_superuser:
            result += "<span title='É um simples colaborador, sem acesso ao admin.'>👨</span>"
        return mark_safe(f"<span style='font-size: 150%'>{result}</span>")
