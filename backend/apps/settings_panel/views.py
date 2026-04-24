from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model

from apps.tenants.models import TenantMembership
from apps.tenants.permissions import user_can_manage_tenant
from apps.rbac.models import TenantUserRole, Role

from .forms import AddMemberForm, UpdateMemberRoleForm, AssignRBACRoleForm
from apps.auditlog.services import log_event

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

            membership, created = TenantMembership.objects.update_or_create(
            tenant=tenant,
            user=user,
            defaults={"role": role, "is_active": True},
            )

            log_event(
                tenant=tenant,
                actor=request.user,
                request=request,
                action="create" if created else "update",
                message=f"Member {'added' if created else 'updated'}: {user.email} as {role}",
                object_type="TenantMembership",
                object_id=membership.id,
                meta={
                    "target_user_email": user.email,
                    "role": role,
                    "created": created,
                },
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

    old_role = membership.role

    if request.method == "POST":
        form = UpdateMemberRoleForm(request.POST)
        if form.is_valid():
            membership.role = form.cleaned_data["role"]
            membership.save(update_fields=["role"])
            messages.success(request, "Member role updated.")

            log_event(
                tenant=tenant,
                actor=request.user,
                request=request,
                action="update",
                message=f"Member role updated: {membership.user.email} {old_role} -> {membership.role}",
                object_type="TenantMembership",
                object_id=membership.id,
                meta={
                    "target_user_email": membership.user.email,
                    "old_role": old_role,
                    "new_role": membership.role,
                },
            )

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
        log_event(
            tenant=tenant,
            actor=request.user,
            request=request,
            action="update",
            message=f"Member deactivated: {membership.user.email}",
            object_type="TenantMembership",
            object_id=membership.id,
            meta={
                "target_user_email": membership.user.email,
                "role": membership.role,
                "is_active": False,
            },
        )
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

    available_roles = Role.objects.filter(
        tenant=tenant,
        is_active=True
    ).order_by("code")

    return render(request, "settings_panel/roles.html", {
        "roles": roles,
        "available_roles": available_roles,
    })


@login_required
def assign_rbac_role(request):
    tenant = _get_tenant_or_forbid(request)
    if tenant is None:
        return HttpResponseForbidden("No tenant selected.")
    if not _require_settings_access(request, tenant):
        return HttpResponseForbidden("You do not have access to assign roles.")

    if request.method == "POST":
        form = AssignRBACRoleForm(request.POST, tenant=tenant)
        if form.is_valid():
            email = form.cleaned_data["user_email"].lower()
            role_id = form.cleaned_data["role_id"]

            user = User.objects.filter(email=email).first()
            role = Role.objects.filter(id=role_id, tenant=tenant, is_active=True).first()

            if not user:
                messages.error(request, "User does not exist yet.")
                return redirect("settings_panel:roles")

            assignment, created = TenantUserRole.objects.update_or_create(
                tenant=tenant,
                user=user,
                defaults={"role": role, "is_active": True},
            )

            log_event(
                tenant=tenant,
                actor=request.user,
                request=request,
                action="create" if created else "update",
                message=f"RBAC role {'assigned' if created else 'updated'}: {user.email} -> {role.code}",
                object_type="TenantUserRole",
                object_id=assignment.id,
                meta={
                    "target_user_email": user.email,
                    "role_code": role.code,
                    "created": created,
                },
            )

            messages.success(request, f"{user.email} assigned to {role.name}.")
            return redirect("settings_panel:roles")

    return redirect("settings_panel:roles")

@login_required
def deactivate_rbac_role(request, assignment_id):
    tenant = _get_tenant_or_forbid(request)
    if tenant is None:
        return HttpResponseForbidden("No tenant selected.")
    if not _require_settings_access(request, tenant):
        return HttpResponseForbidden("You do not have access to update roles.")

    assignment = get_object_or_404(TenantUserRole, id=assignment_id, tenant=tenant)

    if request.method == "POST":
        assignment.is_active = False
        assignment.save(update_fields=["is_active"])

        log_event(
            tenant=tenant,
            actor=request.user,
            request=request,
            action="update",
            message=f"RBAC role deactivated: {assignment.user.email} -> {assignment.role.code}",
            object_type="TenantUserRole",
            object_id=assignment.id,
            meta={
                "target_user_email": assignment.user.email,
                "role_code": assignment.role.code,
                "is_active": False,
            },
        )

        messages.success(request, "RBAC role assignment deactivated.")

    return redirect("settings_panel:roles")