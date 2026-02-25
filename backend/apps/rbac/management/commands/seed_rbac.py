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
    "fellow": [
        # fellows typically view only their own data; enforce with object-level checks later
        "timesheets.view",
    ],
    "cho": [
        # cho typically approves or views student timesheets assigned to them; object-level checks later
        "timesheets.view",
    ],
}

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

        # permissions
        perm_map = {}
        for code, name in DEFAULT_PERMS:
            perm, _ = Permission.objects.get_or_create(code=code, defaults={"name": name})
            perm_map[code] = perm

        # roles + role-perms
        for role_code, perm_codes in DEFAULT_ROLES.items():
            role, _ = Role.objects.get_or_create(
                tenant=tenant,
                code=role_code,
                defaults={"name": role_code.replace("_", " ").title()},
            )
            for pcode in perm_codes:
                RolePermission.objects.get_or_create(role=role, permission=perm_map[pcode])

        self.stdout.write(self.style.SUCCESS(f"Seeded RBAC for tenant '{tenant.slug}'"))