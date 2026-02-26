from django.core.management.base import BaseCommand
from django.apps import apps
from apps.tenants.models import Tenant

def _audit(tenant, message: str, *, action: str = "create", actor=None, actor_email: str = "system", meta: dict | None = None):
    """Best-effort audit logger for management commands."""
    try:
        AuditLogEntry = apps.get_model("auditlog", "AuditLogEntry")
        if AuditLogEntry is None:
            return

        AuditLogEntry.objects.create(
            tenant=tenant,
            actor=actor,
            actor_email=actor_email,
            action=action,
            message=message,
            meta=meta or {},
        )
    except Exception:
        # audit logging should never block command execution
        return

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

        _audit(
            tenant,
            f"Tenant created via create_tenant command: {tenant.name} ({tenant.slug})",
            action="create",
            actor=None,
            actor_email="system",
            meta={
                "tenant_id": str(tenant.id),
                "tenant_slug": tenant.slug,
                "tenant_name": tenant.name,
                "source": "management_command:create_tenant",
            },
        )

        self.stdout.write(self.style.SUCCESS(f"Created tenant: {tenant.name} ({tenant.slug})"))