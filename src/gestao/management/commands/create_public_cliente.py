from django.core import exceptions
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from django.utils.encoding import force_str
from django_tenants.utils import get_tenant_model, get_tenant_domain_model
from gestao.models import Cliente, Dominio

class Command(BaseCommand):
    help = 'Create a tenant'

    def handle(self, *args, **options):
        try:
            cliente, created = Cliente.objects.get_or_create(
                schema_name='public',
                defaults={"name": "Public Client"},
            )
            if created:         
                try:
                    dominio = Dominio(tenant=cliente, domain='integrador', is_primary=True)
                    dominio.save()
                except IntegrityError as e:
                    print(f"Error creating domain: {force_str(e)}")
        except IntegrityError as e:
            print(f"Error creating tenant: {force_str(e)}")
