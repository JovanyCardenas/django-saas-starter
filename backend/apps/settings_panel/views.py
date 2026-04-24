from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model

from apps.tenants.models import TenantMembership
from apps.tenants.permissions import user_can_manage_tenant
from apps.rbac.models import TenantUserRole

from .forms import AddMemberForm, UpdateMemberRoleForm

User = get_user_model()


@login_required
def add_member(request):
    tenant = _get_tenant_or_forbid(request)
    if tenant is None:
        return HttpResponseForbidden("No tenant selected.")
    if not _require_settings_access(request, tenant):
        return HttpResponseForbidden("You do not have access to add members.")

    if request.method == "POST":
        form = AddMemberForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].lower()
            role = form.cleaned_data["role"]

            user = User.objects.filter(email=email).first()
            if not user:
                messages.error(request, "User does not exist yet. Create the user first.")
                return redirect("settings_panel:members")

            TenantMembership.objects.update_or_create(
                tenant=tenant,
                user=user,
                defaults={"role": role, "is_active": True},
            )

            messages.success(request, f"{email} added as {role}.")
            return redirect("settings_panel:members")

    return redirect("settings_panel:members")


@login_required
def update_member_role(request, membership_id):
    tenant = _get_tenant_or_forbid(request)
    if tenant is None:
        return HttpResponseForbidden("No tenant selected.")
    if not _require_settings_access(request, tenant):
        return HttpResponseForbidden("You do not have access to update members.")

    membership = get_object_or_404(TenantMembership, id=membership_id, tenant=tenant)

    if request.method == "POST":
        form = UpdateMemberRoleForm(request.POST)
        if form.is_valid():
            membership.role = form.cleaned_data["role"]
            membership.save(update_fields=["role"])
            messages.success(request, "Member role updated.")

    return redirect("settings_panel:members")


@login_required
def deactivate_member(request, membership_id):
    tenant = _get_tenant_or_forbid(request)
    if tenant is None:
        return HttpResponseForbidden("No tenant selected.")
    if not _require_settings_access(request, tenant):
        return HttpResponseForbidden("You do not have access to deactivate members.")

    membership = get_object_or_404(TenantMembership, id=membership_id, tenant=tenant)

    if request.method == "POST":
        membership.is_active = False
        membership.save(update_fields=["is_active"])
        messages.success(request, "Member deactivated.")

    return redirect("settings_panel:members")


def _get_tenant_or_forbid(request):
    tenant = getattr(request, "tenant", None)
    if tenant is None:
        return None
    return tenant


def _require_settings_access(request, tenant):
    if not user_can_manage_tenant(request.user, tenant):
        return False
    return True


@login_required
def organization_settings(request):
    tenant = _get_tenant_or_forbid(request)
    if tenant is None:
        return HttpResponseForbidden("No tenant selected.")

    if not _require_settings_access(request, tenant):
        return HttpResponseForbidden("You do not have access to organization settings.")

    return render(request, "settings_panel/organization.html", {
        "tenant": tenant,
    })


@login_required
def member_settings(request):
    tenant = _get_tenant_or_forbid(request)
    if tenant is None:
        return HttpResponseForbidden("No tenant selected.")

    if not _require_settings_access(request, tenant):
        return HttpResponseForbidden("You do not have access to members.")

    memberships = TenantMembership.objects.filter(
        tenant=tenant
    ).select_related("user").order_by("user__email")

    return render(request, "settings_panel/members.html", {
        "memberships": memberships,
    })


@login_required
def role_settings(request):
    tenant = _get_tenant_or_forbid(request)
    if tenant is None:
        return HttpResponseForbidden("No tenant selected.")

    if not _require_settings_access(request, tenant):
        return HttpResponseForbidden("You do not have access to roles.")

    roles = TenantUserRole.objects.filter(
        tenant=tenant
    ).select_related("user", "role").order_by("user__email")

    return render(request, "settings_panel/roles.html", {
        "roles": roles,
    })