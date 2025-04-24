from django.db.models import Model
from django.contrib.admin import register, StackedInline
from import_export.resources import ModelResource
from base.admin import BaseModelAdmin
from coorte.models import Papel, CoorteCurso, CoortePolo, CoortePrograma, Vinculo
from edu.models import Curso, Polo, Programa


####
# Inlines
####
class CoorteBaseInline(StackedInline):
    model: Model = CoorteCurso
    extra: int = 0
    verbose_name = "Coorte"
    verbose_name_plural = "Coortes"
    contexto = None

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'papel':
            field.queryset = field.queryset.filter(contexto=self.contexto)
        return field


class CoorteCursoInline(CoorteBaseInline):
    model: Model = CoorteCurso
    extra: int = 0
    verbose_name = "Coorte"
    verbose_name_plural = "Coortes"
    contexto = Papel.Contexto.CURSO


class CoortePoloInline(CoorteBaseInline):
    model: Model = CoortePolo
    extra: int = 0
    verbose_name = "Coorte"
    verbose_name_plural = "Coortes"
    contexto = Papel.Contexto.POLO


class CoorteProgramaInline(CoorteBaseInline):
    model: Model = CoortePrograma
    extra: int = 0
    verbose_name = "Coorte"
    verbose_name_plural = "Coortes"
    contexto = Papel.Contexto.PROGRAMA


class VinculoInline(StackedInline):
    model: Model = Vinculo
    extra: int = 0


####
# Admins
####
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
    inlines = [CoorteCursoInline]


@register(Polo)
class PoloAdmin(BaseModelAdmin):
    class PoloResource(ModelResource):
        class Meta:
            model = Polo
            export_order = ["suap_id", "nome"]
            import_id_fields = ("suap_id",)
            fields = export_order
            skip_unchanged = True

    list_display = ["codigo", "nome"]
    search_fields = ["codigo", "nome", "suap_id"]
    resource_classes = [PoloResource]
    inlines = [CoortePoloInline]


@register(Programa)
class ProgramaAdmin(BaseModelAdmin):
    class ProgramaResource(ModelResource):
        class Meta:
            model = Programa
            export_order = ["suap_id", "nome", "sigla"]
            import_id_fields = ("suap_id",)
            fields = export_order
            skip_unchanged = True

    list_display = ["sigla", "nome"]
    search_fields = ["nome", "suap_id", "sigla"]
    resource_classes = [ProgramaResource]
    inlines = [CoorteProgramaInline]
