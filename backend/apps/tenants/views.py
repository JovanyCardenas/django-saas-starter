from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import TenantMembership
from .middleware import SESSION_TENANT_KEY


# from apps.tenants.utils import require_tenant

# # Anywhere you want to require a tenant selected:
# @require_tenant
# def dashboard(request):
#     tenant = request.tenant
#     ...

@login_required
def choose_tenant(request):
    memberships = (
        TenantMembership.objects
        .select_related("tenant")
        .filter(user=request.user, is_active=True, tenant__is_active=True)
        .order_by("tenant__name")
    )

    if request.method == "POST":
        tenant_id = request.POST.get("tenant_id")
        if tenant_id and memberships.filter(tenant_id=tenant_id).exists():
            request.session[SESSION_TENANT_KEY] = str(tenant_id)
            return redirect("home")  # change to your dashboard route name

    # Auto-redirect if exactly one tenant
    if memberships.count() == 1:
        request.session[SESSION_TENANT_KEY] = str(memberships.first().tenant_id)
        return redirect("home")

    return render(request, "tenants/choose.html", {"memberships": memberships})


@login_required
def clear_tenant(request):
    request.session.pop(SESSION_TENANT_KEY, None)
    return redirect("tenants:choose")