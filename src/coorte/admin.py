from django.utils.translation import gettext as _
from django.db.models import Model
from django.contrib.auth.models import User
from django.contrib.admin import register, StackedInline
from import_export.resources import ModelResource
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget
from base.admin import BaseModelAdmin
from edu.models import Curso, Polo, Programa
from coorte.models import Papel, Coorte, Vinculo, CoorteCurso, CoortePolo, CoortePrograma


####
# Inlines
####


class VinculoInline(StackedInline):
    model: Model = Vinculo
    extra: int = 0


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


@register(Coorte)
class CoorteAdmin(BaseModelAdmin):
    class CoorteResource(ModelResource):
        papel = Field(attribute="papel", column_name="papel", widget=ForeignKeyWidget(Papel, field="papel"))

    resource_classes = [CoorteResource]
    list_display = ["papel", "instancia"]
    readonly_fields = ["instancia"]

    def instancia(self, obj):
        if isinstance(obj, CoorteCurso):
            return obj.curso.nome
        if isinstance(obj, CoortePolo):
            return obj.polo.nome
        if isinstance(obj, CoortePrograma):
            return obj.programa.sigla

    instancia.short_description = "Instância"


@register(CoorteCurso)
class CoorteCursoAdmin(BaseModelAdmin):
    class CoorteCursoResource(ModelResource):
        curso = Field(
            attribute="curso",
            column_name="curso",
            widget=ForeignKeyWidget(Curso, field="id"),
        )

    list_display = ["curso"]
    inlines = [VinculoInline]


@register(CoortePolo)
class CoortePoloResourceAdmin(BaseModelAdmin):
    class CoortePoloResource(ModelResource):
        polo = Field(
            attribute="polo",
            column_name="polo",
            widget=ForeignKeyWidget(Polo, field="id"),
        )

    list_display = ["polo"]
    inlines = [VinculoInline]


@register(CoortePrograma)
class CoorteProgramaAdmin(BaseModelAdmin):
    class CoorteProgramaResource(ModelResource):
        programa = Field(
            attribute="programa",
            column_name="programa",
            widget=ForeignKeyWidget(Programa, field="id"),
        )

    list_display = ["programa"]
    inlines = [VinculoInline]


@register(Vinculo)
class VinculoAdmin(BaseModelAdmin):
    class VinculoResource(ModelResource):
        colaborador = Field(
            attribute="colaborador",
            column_name="colaborador",
            widget=ForeignKeyWidget(User, field="username"),
        )
        coorte = Field(attribute="coorte", column_name="coorte", widget=ForeignKeyWidget(Coorte, field="id"))

    resource_classes = [VinculoResource]
    list_display = ["colaborador", "coorte", "cursos", "polos", "programas"]
    readonly_fields = ["cursos", "programas", "polos"]

    def cursos(self, obj):
        coorte_cursos = CoorteCurso.objects.filter(coorte_ptr_id=obj.coorte_id)
        return ", ".join([cc.curso.nome for cc in coorte_cursos])

    def polos(self, obj):
        coorte_polos = CoortePolo.objects.filter(coorte_ptr_id=obj.coorte_id)
        return ", ".join([cp.polo.nome for cp in coorte_polos])

    def programas(self, obj):
        coorte_programas = CoortePrograma.objects.filter(coorte_ptr_id=obj.coorte_id)
        return ", ".join([cpr.programa.nome for cpr in coorte_programas])

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "coorte",
                    "colaborador",
                )
            },
        ),
        (
            "Cursos Associados",
            {
                "fields": ("cursos",),
            },
        ),
        (
            "Polos Associados",
            {
                "fields": ("polos",),
            },
        ),
        (
            "Programas Associados",
            {
                "fields": ("programas",),
            },
        ),
    )

    cursos.short_description = "Cursos"
    polos.short_description = "Polos"
    programas.short_description = "Programas"
