from apps.tenants.models import TenantMembership


ADMIN_ROLES = {
    TenantMembership.Role.OWNER,
    TenantMembership.Role.ADMIN,
    TenantMembership.Role.STAFF,
}


def user_can_manage_tenant(user, tenant) -> bool:
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return TenantMembership.objects.filter(
        user=user,
        tenant=tenant,
        is_active=True,
        role__in=ADMIN_ROLES,
    ).exists()