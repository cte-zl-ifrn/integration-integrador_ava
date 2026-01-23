from django.utils.translation import gettext as _
from django.utils.safestring import mark_safe
from django.db.models import Model
from django.contrib.admin import register, display, site, StackedInline
from django.contrib.auth.models import User, Group, Permission
from import_export.resources import ModelResource
from import_export.widgets import ManyToManyWidget
from import_export.fields import Field
from base.admin import BaseModelAdmin
from coorte.models import Enrolment


####
# Hacks
####

site.unregister(Group)
site.unregister(User)


####
# Inlines
####

class EnrolmentInline(StackedInline):
    model: Model = Enrolment
    extra: int = 0
    autocomplete_fields = ["cohort"]


####
# Admins
####

@register(Group)
class GroupAdmin(BaseModelAdmin):
    class GroupResource(ModelResource):
        permissions = Field(
            attribute='permissions',
            widget=ManyToManyWidget(Permission, field='codename', separator='|')
        )
        class Meta:
            model = Group
            export_order = ["name","permissions"]
            import_id_fields = ("name",)
            fields = export_order
            skip_unchanged = True

    list_display = ["name"]
    search_fields = ["name"]
    resource_classes = [GroupResource]


@register(User)
class UserAdmin(BaseModelAdmin):
    class UserResource(ModelResource):
        groups = Field(
            attribute='groups',
            widget=ManyToManyWidget(Permission, field='name', separator='|')
        )
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
    autocomplete_fields: list[str] = ['groups']
    inlines = [EnrolmentInline]
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
        if obj.groups.count() > 0:
            plural = "nos grupos" if obj.groups.count() > 1 else "no grupo"
            grupos = ", ".join([f"'{g.name}'" for g in obj.groups.all()])
            result += f"<span title=\"Está {plural} {grupos}.\">👥</span>"
            
        return mark_safe(f"<span style='font-size: 150%'>{result}</span>")
