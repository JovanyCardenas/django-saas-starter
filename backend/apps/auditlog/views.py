from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import render

from .models import AuditLogEntry


@login_required
def audit_home(request):
    """
    Tenant-scoped audit log list.

    Access policy (starter): staff-only.
    Later, swap this to your tenant RBAC permission checks.
    """

    tenant = getattr(request, "tenant", None)
    if tenant is None:
        return HttpResponseForbidden("No tenant selected.")

    # Starter access control: Django staff users only
    if not request.user.is_staff:
        return HttpResponseForbidden("You do not have access to the audit log.")

    qs = (
        AuditLogEntry.objects.filter(tenant=tenant)
        .select_related("actor")
        .order_by("-created_at")
    )

    paginator = Paginator(qs, 50)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "auditlog/audit_home.html",
        {"entries": page_obj.object_list, "page_obj": page_obj},
    )