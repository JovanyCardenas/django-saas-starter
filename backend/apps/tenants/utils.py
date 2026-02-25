from __future__ import annotations

from functools import wraps
from django.http import HttpRequest, HttpResponseForbidden
from django.shortcuts import redirect
from .models import TenantMembership


def require_tenant(view_func):
    """
    Ensures request.tenant is set; otherwise redirects to tenant selection page.
    """
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        if getattr(request, "tenant", None) is None:
            return redirect("tenants:choose")
        return view_func(request, *args, **kwargs)
    return _wrapped


def require_tenant_role(*allowed_roles: str):
    """
    Require the current user to have a specific role within request.tenant.
    Usage: @require_tenant_role("owner", "admin")
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request: HttpRequest, *args, **kwargs):
            tenant = getattr(request, "tenant", None)
            if tenant is None:
                return redirect("tenants:choose")

            membership = TenantMembership.objects.filter(
                tenant=tenant, user=request.user, is_active=True
            ).first()

            if not membership or membership.role not in allowed_roles:
                return HttpResponseForbidden("You do not have permission to access this resource.")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator