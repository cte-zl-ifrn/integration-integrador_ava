from django.db.models import CharField, DateField, BooleanField
from django_tenants.models import TenantMixin, DomainMixin


class ActiveMixin:
    @property
    def active_icon(self):
        return "✅" if self.active else "⛔"


class Client(TenantMixin):
    name = CharField(max_length=256)
    created_on = DateField(auto_now_add=True)

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True


class Domain(DomainMixin):
    pass