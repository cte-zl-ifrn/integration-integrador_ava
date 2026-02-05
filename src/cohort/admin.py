from django.utils.translation import gettext as _
from django.db.models import Model
from django.contrib.admin import register, StackedInline, SimpleListFilter
from import_export.resources import ModelResource
from base.admin import BasicModelAdmin, BaseModelAdmin
from cohort.models import Role, Cohort, Enrolment


####
# Inlines
####

class EnrolmentInline(StackedInline):
    model: Model = Enrolment
    extra: int = 0
    autocomplete_fields = ["user"]


####
# Admins
####

@register(Role)
class RoleAdmin(BaseModelAdmin):
    class RoleResource(ModelResource):
        class Meta:
            model = Role
            export_order = ["name", "shortname", "active"]
            import_id_fields = ("shortname",)
            fields = export_order
            skip_unchanged = True

    list_display = ["name", "shortname", "active"]
    list_filter = ["active",] + BaseModelAdmin.list_filter
    search_fields = ["name", "shortname"]
    resource_classes = [RoleResource]


@register(Cohort)
class CohortAdmin(BasicModelAdmin):
    list_display = ["name", "idnumber", "rule_diario", "rule_coordenacao", "active"]
    search_fields = ["name", "idnumber"]
    list_filter = ["active"]
    fieldsets = (
        (_("Informações Básicas"), {
            'fields': (('name', 'idnumber', 'active'), 'role')
        }),
        (_("Regras de Validação"), {
            'fields': ("rule_diario", "rule_coordenacao",),
            'classes': ('wide',),
            'description': _('Configure a regra para validar quando este coorte deve ser sincronizado no diário')
        }),
        (_("Descrição"), {
            'fields': ('description',)
        }),
    )
    inlines = [EnrolmentInline]
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Garante que o RuleField use o widget correto."""
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        return formfield
