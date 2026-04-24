from django.apps import apps
from django.core.management.base import BaseCommand

from apps.tenants.models import Tenant
from apps.rbac.models import Permission, Role, RolePermission

DEFAULT_PERMS = [
    ("applications.view", "View applications"),
    ("applications.review", "Review/score applications"),
    ("interviews.view", "View interviews"),
    ("interviews.score", "Score interviews"),
    ("placements.manage", "Manage placements"),
    ("timesheets.view", "View timesheets"),
    ("timesheets.approve", "Approve timesheets"),
    ("requirements.manage", "Manage requirements"),
    ("users.manage", "Manage users"),
    ("settings.manage", "Manage settings"),
]

DEFAULT_ROLES = {
    # role_code: [perm_codes...]
        "owner": [
        "applications.view", "applications.review",
        "interviews.view", "interviews.score",
        "placements.manage",
        "timesheets.view", "timesheets.approve",
        "requirements.manage",
        "users.manage",
        "settings.manage",
    ],
    "admin": [
        "applications.view", "applications.review",
        "interviews.view", "interviews.score",
        "placements.manage",
        "timesheets.view", "timesheets.approve",
        "requirements.manage",
        "users.manage",
        "settings.manage",
    ],
    "staff_admin": [
        "applications.view", "applications.review",
        "interviews.view", "interviews.score",
        "placements.manage",
        "timesheets.view", "timesheets.approve",
        "requirements.manage",
        "users.manage",
    ],
    "program_staff": [
        "applications.view", "applications.review",
        "interviews.view", "interviews.score",
        "placements.manage",
        "timesheets.view", "timesheets.approve",
        "requirements.manage",
    ],
    "support_staff": [
        "applications.view",
        "interviews.view",
        "timesheets.view",
        "requirements.manage",
    ],
    # "fellow": [
    #     # fellows typically view only their own data; enforce with object-level checks later
    #     "timesheets.view",
    # ],
    # "cho": [
    #     # cho typically approves or views student timesheets assigned to them; object-level checks later
    #     "timesheets.view",
    # ],
}


def _audit(tenant: Tenant, message: str, *, meta: dict | None = None):
    """Best-effort audit log writer for management commands."""
    AuditLogEntry = apps.get_model("auditlog", "AuditLogEntry")
    if AuditLogEntry is None:
        return

    AuditLogEntry.objects.create(
        tenant=tenant,
        actor=None,
        actor_email="system",
        action="system",
        message=message,
        meta=meta or {},
    )


class Command(BaseCommand):
    help = "Seed default permissions and roles for a given tenant slug."

    def add_arguments(self, parser):
        parser.add_argument("tenant_slug", type=str)

    def handle(self, *args, **options):
        tenant_slug = options["tenant_slug"]
        tenant = Tenant.objects.filter(slug=tenant_slug).first()
        if not tenant:
            self.stderr.write(self.style.ERROR(f"Tenant '{tenant_slug}' not found."))
            return

        created_perms = 0
        created_roles = 0
        created_role_perms = 0

        # permissions
        perm_map = {}
        for code, name in DEFAULT_PERMS:
            perm, created = Permission.objects.get_or_create(code=code, defaults={"name": name})
            if created:
                created_perms += 1
            perm_map[code] = perm

        # roles + role-perms
        for role_code, perm_codes in DEFAULT_ROLES.items():
            role, created = Role.objects.get_or_create(
                tenant=tenant,
                code=role_code,
                defaults={"name": role_code.replace("_", " ").title()},
            )
            if created:
                created_roles += 1
            for pcode in perm_codes:
                _, created = RolePermission.objects.get_or_create(role=role, permission=perm_map[pcode])
                if created:
                    created_role_perms += 1

        _audit(
            tenant,
            f"Seeded RBAC for tenant '{tenant.slug}'",
            meta={
                "tenant_slug": tenant.slug,
                "created_permissions": created_perms,
                "created_roles": created_roles,
                "created_role_permissions": created_role_perms,
                "default_perm_count": len(DEFAULT_PERMS),
                "default_role_count": len(DEFAULT_ROLES),
            },
        )

        self.stdout.write(self.style.SUCCESS(f"Seeded RBAC for tenant '{tenant.slug}'"))