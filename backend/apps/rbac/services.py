from __future__ import annotations

from django.db.models import Q
from apps.tenants.models import TenantMembership
from .models import TenantUserRole, RolePermission


FULL_ACCESS_TENANT_ROLES = {TenantMembership.Role.OWNER, TenantMembership.Role.ADMIN}


def has_full_access(user, tenant) -> bool:
    """
    Owner/Admin at TenantMembership level gets full access.
    """
    return TenantMembership.objects.filter(
        user=user,
        tenant=tenant,
        is_active=True,
        role__in=FULL_ACCESS_TENANT_ROLES,
        tenant__is_active=True,
    ).exists()


def user_role_codes(user, tenant) -> set[str]:
    """
    Returns RBAC role codes assigned to the user within the tenant.
    """
    qs = TenantUserRole.objects.filter(
        user=user,
        tenant=tenant,
        is_active=True,
        role__is_active=True,
        tenant__is_active=True,
    ).select_related("role")
    return {x.role.code for x in qs}


def user_permission_codes(user, tenant) -> set[str]:
    """
    Returns permission codes granted to user via their roles inside the tenant.
    """
    qs = RolePermission.objects.filter(
        role__tenant=tenant,
        role__is_active=True,
        role__user_assignments__user=user,
        role__user_assignments__tenant=tenant,
        role__user_assignments__is_active=True,
    ).select_related("permission")

    return {rp.permission.code for rp in qs}


def has_role(user, tenant, *role_codes: str) -> bool:
    if has_full_access(user, tenant):
        return True
    if not role_codes:
        return False
    roles = user_role_codes(user, tenant)
    return any(rc in roles for rc in role_codes)


def has_perm(user, tenant, perm_code: str) -> bool:
    if has_full_access(user, tenant):
        return True
    perms = user_permission_codes(user, tenant)
    return perm_code in perms