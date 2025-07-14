from django.utils.translation import gettext as _
from django.db.models import CharField, DateField, BooleanField
# from django_tenants.models import TenantMixin, DomainMixin # tenants


class ActiveMixin:
    @property
    def active_icon(self):
        return "✅" if self.active else "⛔"


# # tenants
# class Client(TenantMixin):
#     name = CharField(max_length=256)
#     created_on = DateField(auto_now_add=True)

#     # default true, schema will be automatically created and synced when it is saved
#     auto_create_schema = True

#     class Meta:
#         verbose_name = _("cliente")
#         verbose_name_plural = _("clientes")
#         ordering = ["name"]


# # tenants
# class Domain(DomainMixin):

#     class Meta:
#         verbose_name = _("domínio")
#         verbose_name_plural = _("domínios")
#         ordering = ["domain"]
