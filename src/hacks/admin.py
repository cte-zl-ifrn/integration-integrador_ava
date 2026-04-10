from django.utils.translation import gettext as _
from django.utils.html import format_html, format_html_join
from django.contrib.admin import register, display, site
from django.contrib.auth.models import User, Group, Permission
from import_export.resources import ModelResource
from import_export.widgets import ManyToManyWidget
from import_export.fields import Field
from base.admin import BaseModelAdmin


####
# Hacks
####

site.unregister(Group)
site.unregister(User)


####
# Admins
####


@register(Group)
class GroupAdmin(BaseModelAdmin):
    class GroupResource(ModelResource):
        permissions = Field(
            attribute="permissions", widget=ManyToManyWidget(Permission, field="codename", separator="|")
        )

        class Meta:
            model = Group
            export_order = ["name", "permissions"]
            import_id_fields = ("name",)
            fields = export_order
            skip_unchanged = True

    list_display = ["name"]
    search_fields = ["name"]
    resource_classes = [GroupResource]


@register(User)
class UserAdmin(BaseModelAdmin):
    class UserResource(ModelResource):
        groups = Field(attribute="groups", widget=ManyToManyWidget(Permission, field="name", separator="|"))

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
                "groups",
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
                    "Controla a identidade do usuário nos sistemas, qual seu role e quais suas autorizações."
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
                "fields": ["groups"],
                "description": _("Permissões e grupos aos quais o usuário pertence."),
            },
        ),
    ]
    readonly_fields = ["date_joined", "last_login"]
    autocomplete_fields: list[str] = ["groups"]
    resource_classes = [UserResource]

    @display
    def auth(self, obj):
        badges = [
            (
                format_html("<span title='{}'>{}</span>", "Ativo", "✅")
                if obj.is_active
                else format_html("<span title='{}'>{}</span>", "Inativo", "❌")
            )
        ]
        if obj.is_staff and obj.is_superuser:
            badges.append(format_html("<span title='{}'>{}</span>", "Super usuário", "👮‍♂️"))
        elif obj.is_superuser and not obj.is_staff:
            badges.append(
                format_html(
                    "<span title='{}'>{}</span>",
                    "Super usuário sem permissão de operar o admin? Você configurou certo?",
                    "🕵️‍♂️",
                )
            )
        elif obj.is_staff and not obj.is_superuser:
            badges.append(format_html("<span title='{}'>{}</span>", "Pode operar o admin", "👷‍♂️"))
        elif not obj.is_staff and not obj.is_superuser:
            badges.append(
                format_html("<span title='{}'>{}</span>", "É um simples colaborador, sem acesso ao admin.", "👨")
            )
        if obj.groups.count() > 0:
            plural = "nos grupos" if obj.groups.count() > 1 else "no grupo"
            grupos = ", ".join([f"'{g.name}'" for g in obj.groups.all()])
            badges.append(format_html('<span title="Está {} {}.">👥</span>', plural, grupos))

        return format_html(
            "<span style='font-size: 150%'>{}</span>",
            format_html_join("", "{}", ((b,) for b in badges)),
        )
