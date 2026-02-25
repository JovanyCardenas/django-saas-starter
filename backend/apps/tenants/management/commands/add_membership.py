from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()

class Command(BaseCommand):
    help = "Add a user to a tenant with a tenant membership role (owner/admin/member)."

    def add_arguments(self, parser):
        parser.add_argument("tenant_slug", type=str)
        parser.add_argument("email", type=str)
        parser.add_argument("--role", type=str, default="member")

    def handle(self, *args, **options):
        tenant = Tenant.objects.filter(slug=options["tenant_slug"]).first()
        if not tenant:
            self.stderr.write(self.style.ERROR("Tenant not found."))
            return

        user = User.objects.filter(email=options["email"].lower()).first()
        if not user:
            self.stderr.write(self.style.ERROR("User not found. Create the user first (signup or createsuperuser)."))
            return

        role = options["role"]
        if role not in {c for c, _ in TenantMembership.Role.choices}:
            self.stderr.write(self.style.ERROR(f"Invalid role. Choose from: {[c for c, _ in TenantMembership.Role.choices]}"))
            return

        membership, created = TenantMembership.objects.get_or_create(
            tenant=tenant,
            user=user,
            defaults={"role": role, "is_active": True},
        )
        if not created:
            membership.role = role
            membership.is_active = True
            membership.save()

        self.stdout.write(self.style.SUCCESS(f"{user.email} added to {tenant.slug} as {role}"))