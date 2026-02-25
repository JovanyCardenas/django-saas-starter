from __future__ import annotations

from typing import Optional
from django.http import HttpRequest
from .models import Tenant, TenantMembership


SESSION_TENANT_KEY = "active_tenant_id"


def _get_user_tenants(user) -> list[Tenant]:
    if not user.is_authenticated:
        return []
    memberships = (
        TenantMembership.objects
        .select_related("tenant")
        .filter(user=user, is_active=True, tenant__is_active=True)
    )
    return [m.tenant for m in memberships]


class TenantMiddleware:
    """
    Attaches request.tenant (Tenant | None).

    Selection precedence:
    - URL querystring ?tenant=<slug> (stores tenant in session)
    - Session active tenant
    - Auto-select if the user belongs to exactly 1 tenant
    - Otherwise None
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        request.tenant = None

        if not request.user.is_authenticated:
            return self.get_response(request)

        # 1) querystring selection: ?tenant=slug
        slug = request.GET.get("tenant")
        if slug:
            tenant = Tenant.objects.filter(slug=slug, is_active=True).first()
            if tenant and TenantMembership.objects.filter(user=request.user, tenant=tenant, is_active=True).exists():
                request.session[SESSION_TENANT_KEY] = str(tenant.id)
                request.tenant = tenant
                return self.get_response(request)

        # 2) session selection
        tenant_id = request.session.get(SESSION_TENANT_KEY)
        if tenant_id:
            tenant = Tenant.objects.filter(id=tenant_id, is_active=True).first()
            if tenant and TenantMembership.objects.filter(user=request.user, tenant=tenant, is_active=True).exists():
                request.tenant = tenant
                return self.get_response(request)
            else:
                # stale tenant in session
                request.session.pop(SESSION_TENANT_KEY, None)

        # 3) auto-select if only one tenant
        tenants = _get_user_tenants(request.user)
        if len(tenants) == 1:
            request.session[SESSION_TENANT_KEY] = str(tenants[0].id)
            request.tenant = tenants[0]

        return self.get_response(request)