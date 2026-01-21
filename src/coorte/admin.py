from django.utils.translation import gettext as _
from django.db.models import Model
from django.contrib.auth.models import User
from django.contrib.admin import register, StackedInline, SimpleListFilter
from import_export.resources import ModelResource
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget
from base.admin import BasicModelAdmin, BaseModelAdmin
from edu.models import Curso, Polo, Programa
from coorte.models import Enrolment, Papel, Vinculo, Coorte, CoorteCurso, CoortePolo, CoortePrograma, Cohort


####
# Inlines
####

class VinculoInline(StackedInline):
    model: Model = Vinculo
    extra: int = 0
    autocomplete_fields = ["colaborador"]

class EnrolmentInline(StackedInline):
    model: Model = Enrolment
    extra: int = 0
    autocomplete_fields = ["colaborador"]


####
# Resources
####

class CoorteResource(ModelResource):
    papel = Field("papel", "papel", ForeignKeyWidget(Papel, field="sigla"))
    vinculos = Field(column_name="vinculos")

    def dehydrate_vinculos(self, obj):
        return "|".join(u.username for u in User.objects.filter(enrolment__cohort=obj).distinct())

    def after_save_instance(self, instance, row, **kwargs):
        raw_vinculos = row.get("vinculos")
        if raw_vinculos is None:
            return

        usernames = [v.strip() for v in raw_vinculos.split("|") if v.strip()]
        for user in User.objects.filter(username__in=usernames):
            Enrolment.objects.get_or_create(cohort=instance, colaborador=user)

    def import_row(self, row, instance_loader, **kwargs):
        return super().import_row(row, instance_loader, **kwargs)



####
# Filters
####

class PapelFilter(SimpleListFilter):
    title = _("papel")
    parameter_name = "papel"
    contexto = None

    def lookups(self, request, model_admin):
        qs = Papel.objects.filter(contexto=self.contexto)
        return [(p.id, str(p)) for p in qs]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(papel_id=self.value())
        return queryset



####
# Admins
####

@register(Papel)
class PapelAdmin(BaseModelAdmin):
    class PapelResource(ModelResource):
        class Meta:
            model = Papel
            export_order = ["contexto", "papel", "sigla", "nome", "active"]
            import_id_fields = ("sigla",)
            fields = export_order
            skip_unchanged = True

    list_display = ["nome", "contexto", "papel", "sigla", "exemplo", "active"]
    list_filter = ["active", "contexto"] + BaseModelAdmin.list_filter
    search_fields = ["papel", "sigla", "nome"]
    resource_classes = [PapelResource]


@register(CoorteCurso)
class CoorteCursoAdmin(BaseModelAdmin):
    class CoorteCursoResource(CoorteResource):
        curso = Field("curso", "curso", ForeignKeyWidget(Curso, field="codigo"))

        class Meta:
            model = CoorteCurso
            import_id_fields = ["papel","curso"]
            export_order = ["papel","curso", "vinculos"]
            fields = export_order
            skip_unchanged = True

    class PapelCursoFilter(PapelFilter):
        contexto = Papel.Contexto.CURSO

    list_display = ["curso", "papel"]
    list_filter = [PapelCursoFilter]
    search_fields = ["curso__nome", "curso__codigo"]
    autocomplete_fields = ["curso"]
    inlines = [VinculoInline]
    resource_classes = [CoorteCursoResource]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        print(db_field.name)
        if db_field.name == "papel":
            kwargs["queryset"] = Papel.objects.filter(contexto=Papel.Contexto.CURSO)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@register(CoortePolo)
class CoortePoloResourceAdmin(BaseModelAdmin):
    class CoortePoloResource(CoorteResource):
        polo = Field("polo", "polo", ForeignKeyWidget(Polo, field="nome"))

        class Meta:
            model = CoortePolo
            import_id_fields = ["papel","polo"]
            export_order = ["papel","polo", "vinculos"]
            fields = export_order
            skip_unchanged = True

    class PapelPoloFilter(PapelFilter):
        contexto = Papel.Contexto.POLO

    list_display = ["polo", "papel"]
    list_filter = [PapelPoloFilter]
    search_fields = ["polo__nome"]
    autocomplete_fields = ["polo"]
    inlines = [VinculoInline]
    resource_classes = [CoortePoloResource]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        print(db_field.name)
        if db_field.name == "papel":
            kwargs["queryset"] = Papel.objects.filter(contexto=Papel.Contexto.POLO)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@register(CoortePrograma)
class CoorteProgramaAdmin(BaseModelAdmin):
    class CoorteProgramaResource(CoorteResource):
        programa = Field("programa", "programa", ForeignKeyWidget(Programa, field="sigla"))

        class Meta:
            model = CoortePrograma
            import_id_fields = ["papel","programa"]
            export_order = ["papel","programa", "vinculos"]
            fields = export_order
            skip_unchanged = True

    class PapelProgramaFilter(PapelFilter):
        contexto = Papel.Contexto.PROGRAMA

    list_display = ["programa", "papel"]
    list_filter = [PapelProgramaFilter]
    search_fields = ["programa__sigla", "programa__nome"]
    autocomplete_fields = ["programa"]
    inlines = [VinculoInline]
    resource_classes = [CoorteProgramaResource]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        print(db_field.name)
        if db_field.name == "papel":
            kwargs["queryset"] = Papel.objects.filter(contexto=Papel.Contexto.PROGRAMA)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@register(Coorte)
class CoorteAdmin(BasicModelAdmin):
    list_display = ["papel"]
    search_fields = ["papel__papel", "papel__sigla", "papel__nome"]
    readonly_fields = ["papel"]

@register(Cohort)
class CohortAdmin(BasicModelAdmin):
    list_display = ["name", "idnumber", "rule_diario", "rule_coordenacao", "visible"]
    search_fields = ["name", "idnumber"]
    list_filter = ["visible"]
    fieldsets = (
        (_("Informações Básicas"), {
            'fields': (('name', 'idnumber', 'visible'), 'papel')
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
