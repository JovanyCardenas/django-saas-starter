from django.apps import apps

def get_user_role_for_tenant(user, tenant):
    """
    Returns the role code/name for a user within a tenant.
    """
    RoleAssignment = None

    rbac_app = apps.get_app_config("rbac")
    for model in rbac_app.get_models():
        field_names = {f.name for f in model._meta.get_fields()}
        if "role" in field_names and "user" in field_names and "tenant" in field_names:
            RoleAssignment = model
            break

    if not RoleAssignment:
        return None

    assignment = RoleAssignment.objects.filter(
        user=user,
        tenant=tenant
    ).select_related("role").first()

    if not assignment:
        return None

    # Try common identifiers
    for field in ("code", "slug", "name"):
        if hasattr(assignment.role, field):
            return getattr(assignment.role, field)

    return str(assignment.role)