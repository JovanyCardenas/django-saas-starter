from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from apps.tenants.models import TenantMembership
from apps.rbac.models import TenantUserRole


@login_required
def organization_settings(request):
    if not getattr(request, "tenant", None):
        return HttpResponseForbidden("No tenant selected.")

    return render(request, "settings_panel/organization.html", {
        "tenant": request.tenant,
    })


@login_required
def member_settings(request):
    if not getattr(request, "tenant", None):
        return HttpResponseForbidden("No tenant selected.")

    memberships = TenantMembership.objects.filter(
        tenant=request.tenant
    ).select_related("user")

    return render(request, "settings_panel/members.html", {
        "memberships": memberships,
    })


@login_required
def role_settings(request):
    if not getattr(request, "tenant", None):
        return HttpResponseForbidden("No tenant selected.")

    roles = TenantUserRole.objects.filter(
        tenant=request.tenant
    ).select_related("user", "role")

    return render(request, "settings_panel/roles.html", {
        "roles": roles,
    })