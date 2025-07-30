from django.utils.translation import gettext as _
from django.utils.html import format_html
from django.db.models import Model
from django.contrib.admin import register, display, TabularInline
from django_tenants.admin import TenantAdminMixin  # tenants
from base.admin import BaseModelAdmin
from gestao.models import Cliente, Dominio


@register(Cliente)  # tenants
class ClienteAdmin(TenantAdminMixin, BaseModelAdmin):
    class DomainInline(TabularInline):
        model: Model = Dominio
        extra: int = 0
        verbose_name = "Domínio"
        verbose_name_plural = "Domínios"

    list_display = ("name", "dominios", "created_on")
    search_fields = ("name", "domains__domain")
    readonly_fields = ("created_on",)
    inlines = [DomainInline]

    @display(description="Domínios", ordering="domain")
    def dominios(self, obj):
        try:
            domains = ""
            for x in obj.domains.all():
                domain = f"<li>{x.is_primary_icon} {x.domain}</li>"
                domains += f"<a href='https://{x.domain}/'>{domain}</a>" if x.is_primary else domain
            return format_html(f"<ul>{domains}</ul>")
        except Exception as e:
            return f"{e}"
