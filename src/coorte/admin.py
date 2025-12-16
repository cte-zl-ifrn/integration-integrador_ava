from django.utils.translation import gettext as _
from django.db.models import Model
from django.contrib.auth.models import User
from django.contrib.admin import register, StackedInline
from import_export.resources import ModelResource
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from base.admin import BaseModelAdmin
from edu.models import Curso, Polo, Programa
from coorte.models import Papel, Vinculo, CoorteCurso, CoortePolo, CoortePrograma


####
# Inlines
####


class VinculoInline(StackedInline):
    model: Model = Vinculo
    extra: int = 0
    autocomplete_fields = ["colaborador"]


####
# Resources
####


class CoorteResource(ModelResource):
    papel = Field("papel", "papel", ForeignKeyWidget(Papel, field="sigla"))
    vinculos = Field(column_name="vinculos")

    def dehydrate_vinculos(self, obj):
        # exporta no mesmo formato do seu arquivo: username1|username2
        users = User.objects.filter(vinculo__coorte=obj).distinct()
        return "|".join(u.username for u in users)

    def after_save_instance(self, instance, row, **kwargs):
        print(kwargs)

        row = self._current_row  # ver abaixo como preencher isso
        raw_vinculos = row.get("vinculos")
        if raw_vinculos is None:
            return

        usernames = [v.strip() for v in raw_vinculos.split("|") if v.strip()]

        for username in usernames:
            user = User.objects.filter(username=username).first()
            if not user:
                continue
            Vinculo.objects.get_or_create(coorte=instance, colaborador=user)

    def import_row(self, row, instance_loader, **kwargs):
        # guarda a row atual para uso em after_save_instance
        self._current_row = row
        return super().import_row(row, instance_loader, **kwargs)


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

    list_display = ["curso", "papel"]
    list_filter = ["papel"]
    search_fields = ["curso__nome", "curso__codigo"]
    autocomplete_fields = ["papel", "curso"]
    inlines = [VinculoInline]
    resource_classes = [CoorteCursoResource]

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

    list_display = ["polo", "papel"]
    list_filter = ["papel"]
    search_fields = ["polo__nome"]
    autocomplete_fields = ["papel", "polo"]
    inlines = [VinculoInline]
    resource_classes = [CoortePoloResource]


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

    list_display = ["programa", "papel"]
    list_filter = ["papel"]
    search_fields = ["programa__sigla", "programa__nome"]
    autocomplete_fields = ["papel", "programa"]
    inlines = [VinculoInline]
    resource_classes = [CoorteProgramaResource]
