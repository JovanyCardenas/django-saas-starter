from __future__ import annotations

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, CommandError, call_command
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Bootstrap a tenant end-to-end.\n"
        "Creates tenant + owner user + tenant membership + seeds RBAC + assigns RBAC role.\n\n"
        "Example:\n"
        "  python manage.py bootstrap_tenant \"Allan Hancock College\" "
        "--slug allan-hancock --owner-email you@email.com --owner-password \"TempPass123!\""
    )

    def add_arguments(self, parser):
        parser.add_argument("name", type=str, help="Tenant display name")
        parser.add_argument("--slug", required=True, type=str, help="Tenant slug (unique)")
        parser.add_argument("--owner-email", required=True, type=str, help="Owner user's email")

        parser.add_argument("--owner-first-name", default="Owner", type=str)
        parser.add_argument("--owner-last-name", default="User", type=str)

        parser.add_argument(
            "--owner-password",
            default=None,
            type=str,
            help="If omitted, a random password is generated and printed once.",
        )

        parser.add_argument(
            "--membership-role",
            default="owner",
            choices=["owner", "admin", "staff", "member", "viewer"],
            help="TenantMembership.role to set for the owner user (default: owner).",
        )

        parser.add_argument(
            "--skip-rbac",
            action="store_true",
            help="Skip calling seed_rbac and assign_role.",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        name = opts["name"].strip()
        slug = opts["slug"].strip()
        owner_email = opts["owner_email"].strip().lower()
        membership_role = opts["membership_role"]
        skip_rbac = opts["skip_rbac"]

        Tenant = apps.get_model("tenants", "Tenant")
        TenantMembership = apps.get_model("tenants", "TenantMembership")

        # 1) Create or update tenant
        tenant, created = Tenant.objects.get_or_create(
            slug=slug,
            defaults={"name": name},
        )
        if not created and tenant.name != name:
            tenant.name = name
            tenant.save(update_fields=["name"])

        # 2) Create or reuse owner user
        user = User.objects.filter(email=owner_email).first()
        generated_password = None

        if not user:
            password = opts["owner_password"]
            if not password:
                generated_password = User.objects.make_random_password()
                password = generated_password

            user = User.objects.create_user(
                email=owner_email,
                password=password,
                first_name=opts["owner_first_name"],
                last_name=opts["owner_last_name"],
            )

        # 3) Create or update tenant membership
        membership, m_created = TenantMembership.objects.get_or_create(
            tenant=tenant,
            user=user,
            defaults={"role": membership_role, "is_active": True},
        )
        if not m_created:
            changed = False
            if membership.role != membership_role:
                membership.role = membership_role
                changed = True
            if not membership.is_active:
                membership.is_active = True
                changed = True
            if changed:
                membership.save(update_fields=["role", "is_active"])

        # 4) Seed RBAC + assign RBAC role
        # This is separate from TenantMembership.role (your membership role is coarse; RBAC can be granular)
        if not skip_rbac:
            # seed roles/perms for this tenant
            call_command("seed_rbac", slug)

            # assign RBAC "owner" role to the owner user in this tenant
            call_command("assign_role", slug, owner_email, "owner", "--replace")

        # Audit log (non-fatal)
        try:
            from apps.auditlog.services import log_event
            log_event(
                tenant=tenant,
                action="bootstrap_tenant",
                actor=user,
                actor_email=owner_email,
                object_type="Tenant",
                object_id=str(tenant.id),
                message=f"Bootstrapped tenant '{tenant.name}' ({tenant.slug})",
                metadata={"membership_role": membership.role, "skip_rbac": skip_rbac},
            )
        except Exception:
            # audit log should never block bootstrap
            pass

        # Output summary
        self.stdout.write(self.style.SUCCESS(f"Tenant: {tenant.name} ({tenant.slug})"))
        self.stdout.write(self.style.SUCCESS(f"Owner user: {owner_email}"))
        self.stdout.write(self.style.SUCCESS(f"Membership role: {membership.role}"))

        if generated_password:
            self.stdout.write(self.style.WARNING(f"Generated password (save this now): {generated_password}"))