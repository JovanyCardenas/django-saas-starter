from __future__ import annotations

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

User = get_user_model()


def _audit(action: str, tenant, message: str, *, meta: dict | None = None):
    """Best-effort audit log writer.

    Management commands don't have a request, so actor/ip/user-agent aren't available.
    We log as a system event and include structured metadata.
    """
    AuditLogEntry = _get_model("auditlog", "AuditLogEntry")
    if AuditLogEntry is None:
        return  # auditlog app not installed yet
    AuditLogEntry.objects.create(
        tenant=tenant,
        actor=None,
        actor_email="system",
        action=action,
        message=message,
        meta=meta or {},
    )


def _get_model(app_label: str, model_name: str):
    try:
        return apps.get_model(app_label, model_name)
    except LookupError:
        return None


def _get_role_by_identifier(RoleModel, identifier: str):
    """
    Tries to find a Role by common fields: code, slug, name.
    """
    identifier = identifier.strip()

    for field in ("code", "slug", "name"):
        if any(f.name == field for f in RoleModel._meta.get_fields()):
            qs = RoleModel.objects.filter(**{field: identifier})
            role = qs.first()
            if role:
                return role

    # fallback: case-insensitive name
    if any(f.name == "name" for f in RoleModel._meta.get_fields()):
        role = RoleModel.objects.filter(name__iexact=identifier).first()
        if role:
            return role

    return None


def _find_assignment_model():
    """
    Find an RBAC model that looks like (tenant, user, role).
    Works regardless of model name.
    """
    rbac_app = apps.get_app_config("rbac")
    for model in rbac_app.get_models():
        field_names = {f.name for f in model._meta.get_fields()}

        # Must have role + user, and ideally tenant
        if "role" in field_names and "user" in field_names:
            # tenant could be 'tenant' or 'org' in some codebases
            if "tenant" in field_names:
                return model, "tenant"
            if "organization" in field_names:
                return model, "organization"
            if "org" in field_names:
                return model, "org"

    return None, None


class Command(BaseCommand):
    help = "Assign an RBAC role to a user within a tenant. Usage: assign_role <tenant_slug> <email> <role_code>"

    def add_arguments(self, parser):
        parser.add_argument("tenant_slug", type=str)
        parser.add_argument("email", type=str)
        parser.add_argument("role", type=str)

        parser.add_argument(
            "--replace",
            action="store_true",
            help="If the user already has a role assignment in this tenant, replace it.",
        )

    def handle(self, *args, **options):
        tenant_slug = options["tenant_slug"].strip()
        email = options["email"].strip().lower()
        role_identifier = options["role"].strip()
        replace = options["replace"]

        Tenant = _get_model("tenants", "Tenant")
        if Tenant is None:
            raise CommandError("Could not find tenants.Tenant model. Check your tenants app label/model name.")

        tenant = Tenant.objects.filter(slug=tenant_slug).first()
        if not tenant:
            raise CommandError(f"Tenant not found for slug: {tenant_slug}")

        user = User.objects.filter(email=email).first()
        if not user:
            raise CommandError(f"User not found for email: {email}")

        Role = _get_model("rbac", "Role")
        if Role is None:
            raise CommandError("Could not find rbac.Role model. Check your RBAC app label/model name.")

        role = _get_role_by_identifier(Role, role_identifier)
        if not role:
            raise CommandError(f"Role not found for identifier: {role_identifier}")

        AssignmentModel, tenant_field = _find_assignment_model()
        if AssignmentModel is None:
            raise CommandError(
                "Could not find a role assignment model in the rbac app. "
                "Expected a model with fields like (tenant, user, role)."
            )

        # Build lookup for existing assignment(s)
        base_filter = {"user": user, "role": role}
        tenant_filter = {tenant_field: tenant}

        # If your assignment model enforces one-role-per-user-per-tenant,
        # we should lookup by user+tenant and update role.
        # We'll try that first if tenant field exists.
        lookup = {"user": user, **tenant_filter}

        existing = AssignmentModel.objects.filter(**lookup)

        if existing.exists():
            if replace:
                # replace the first row’s role, delete extras if any
                first = existing.first()
                first.role = role
                first.save()
                if existing.count() > 1:
                    existing.exclude(pk=first.pk).delete()
                _audit(
                    "update",
                    tenant,
                    f"RBAC role updated via assign_role: {email} -> {role_identifier}",
                    meta={
                        "tenant_slug": tenant_slug,
                        "target_user_email": email,
                        "role_identifier": role_identifier,
                        "replace": True,
                        "assignment_model": f"{AssignmentModel._meta.app_label}.{AssignmentModel.__name__}",
                    },
                )
                self.stdout.write(self.style.SUCCESS(
                    f"Updated role for {email} in {tenant_slug} to {role_identifier} (replace=True)"
                ))
                return

            # If not replace, ensure role already exists or create additional row
            if existing.filter(role=role).exists():
                _audit(
                    "access",
                    tenant,
                    f"RBAC role assign attempted (no-op): {email} already has {role_identifier}",
                    meta={
                        "tenant_slug": tenant_slug,
                        "target_user_email": email,
                        "role_identifier": role_identifier,
                        "replace": False,
                        "result": "no_op",
                    },
                )
                self.stdout.write(self.style.WARNING(
                    f"{email} already has role {role_identifier} in {tenant_slug}"
                ))
                return

            # Create a second assignment if your schema allows multiple roles
            obj = AssignmentModel.objects.create(user=user, role=role, **tenant_filter)
            _audit(
                "create",
                tenant,
                f"RBAC additional role assigned via assign_role: {email} -> {role_identifier}",
                meta={
                    "tenant_slug": tenant_slug,
                    "target_user_email": email,
                    "role_identifier": role_identifier,
                    "replace": False,
                    "result": "additional_role",
                    "assignment_pk": str(obj.pk),
                    "assignment_model": f"{AssignmentModel._meta.app_label}.{AssignmentModel.__name__}",
                },
            )
            self.stdout.write(self.style.SUCCESS(
                f"Added additional role for {email} in {tenant_slug}: {role_identifier} (pk={obj.pk})"
            ))
            return

        # No assignment exists: create
        obj = AssignmentModel.objects.create(user=user, role=role, **tenant_filter)
        _audit(
            "create",
            tenant,
            f"RBAC role assigned via assign_role: {email} -> {role_identifier}",
            meta={
                "tenant_slug": tenant_slug,
                "target_user_email": email,
                "role_identifier": role_identifier,
                "replace": bool(replace),
                "result": "assigned",
                "assignment_pk": str(obj.pk),
                "assignment_model": f"{AssignmentModel._meta.app_label}.{AssignmentModel.__name__}",
            },
        )
        self.stdout.write(self.style.SUCCESS(
            f"Assigned role {role_identifier} to {email} in {tenant_slug} (pk={obj.pk})"
        ))