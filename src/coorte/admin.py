from django.utils.translation import gettext as _
from django.db.models import Model
# from django.contrib.auth.models import User
from django.contrib.admin import register, StackedInline, SimpleListFilter
from import_export.resources import ModelResource
# from import_export.fields import Field
# from import_export.widgets import ForeignKeyWidget
from base.admin import BasicModelAdmin, BaseModelAdmin
# from edu.models import Curso, Polo, Programa
from coorte.models import Papel, Cohort, Enrolment
# from coorte.models import Vinculo, Coorte, CoorteCurso, CoortePolo, CoortePrograma


####
# Inlines
####

# class VinculoInline(StackedInline):
#     model: Model = Vinculo
#     extra: int = 0
#     autocomplete_fields = ["colaborador"]

class EnrolmentInline(StackedInline):
    model: Model = Enrolment
    extra: int = 0
    autocomplete_fields = ["colaborador"]


####
# Admins
####

@register(Papel)
class PapelAdmin(BaseModelAdmin):
    class PapelResource(ModelResource):
        class Meta:
            model = Papel
            export_order = ["papel", "sigla", "nome", "active"]
            import_id_fields = ("sigla",)
            fields = export_order
            skip_unchanged = True

    list_display = ["nome", "papel", "sigla", "exemplo", "active"]
    list_filter = ["active",] + BaseModelAdmin.list_filter
    search_fields = ["papel", "sigla", "nome"]
    resource_classes = [PapelResource]


@register(Cohort)
class CohortAdmin(BasicModelAdmin):
    list_display = ["name", "idnumber", "rule_diario", "rule_coordenacao", "active"]
    search_fields = ["name", "idnumber"]
    list_filter = ["active"]
    fieldsets = (
        (_("Informações Básicas"), {
            'fields': (('name', 'idnumber', 'active'), 'papel')
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
