from __future__ import annotations

import uuid
from django.conf import settings
from django.db import models


class Permission(models.Model):
    """
    A named permission, e.g.:
      - applications.view
      - applications.review
      - interviews.score
      - timesheets.approve
      - settings.manage
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=120, unique=True)  # permission string
    name = models.CharField(max_length=255)               # human-friendly label
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class Role(models.Model):
    """
    A role is tenant-scoped. Example roles in a tenant:
      - owner
      - admin
      - staff_admin
      - staff
      - support
      - fellow
      - cho
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="roles")

    # machine code like "admin", "staff", "fellow"
    code = models.CharField(max_length=60)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("tenant", "code")]
        ordering = ["tenant__name", "code"]

    def __str__(self) -> str:
        return f"{self.tenant.slug}:{self.code}"


class RolePermission(models.Model):
    """
    Many-to-many join table: Role -> Permission
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="permission_roles")

    class Meta:
        unique_together = [("role", "permission")]

    def __str__(self) -> str:
        return f"{self.role} -> {self.permission.code}"


class TenantUserRole(models.Model):
    """
    Assigns a user a Role in a tenant.
    NOTE: This is separate from TenantMembership.role (Owner/Admin/Member).
    TenantMembership answers: "Are they part of this tenant?"
    TenantUserRole answers: "What RBAC role do they have inside this tenant?"
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="user_roles")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tenant_roles")

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_assignments")

    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("tenant", "user", "role")]
        indexes = [
            models.Index(fields=["tenant", "user"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} -> {self.role}"