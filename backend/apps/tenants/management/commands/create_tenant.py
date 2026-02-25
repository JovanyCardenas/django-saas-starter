from django.core.management.base import BaseCommand
from apps.tenants.models import Tenant

class Command(BaseCommand):
    help = "Create a tenant (organization/school)."

    def add_arguments(self, parser):
        parser.add_argument("name", type=str)
        parser.add_argument("--slug", type=str, default=None)

    def handle(self, *args, **options):
        name = options["name"]
        slug = options["slug"]

        tenant = Tenant(name=name, slug=slug or "")
        tenant.save()

        self.stdout.write(self.style.SUCCESS(f"Created tenant: {tenant.name} ({tenant.slug})"))