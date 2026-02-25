from __future__ import annotations

import uuid
from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Tenant(models.Model):
    """
    Represents a customer/org/school.
    In College Corps: Tenant = School/Organization (e.g., Allan Hancock College)
    In SkillsUSA: Tenant = School/Organization (e.g., Santa Maria HS)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=80, unique=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["slug"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        # Auto-generate slug on create if not provided
        if not self.slug:
            self.slug = slugify(self.name)[:80]
        super().save(*args, **kwargs)


class TenantMembership(models.Model):
    """
    Connects a user to a tenant with a role. One user can belong to many tenants.
    """

    class Role(models.TextChoices):
        OWNER = "owner", "Owner" ##
        ADMIN = "admin", "Admin" ##
        STAFF = "staff", "Staff" ##
        MEMBER = "member", "Member" ## generic org user (actual function decided by product app)
        VIEWER = "viewer", "Viewer"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tenant_memberships")

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    is_active = models.BooleanField(default=True)

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("tenant", "user")]
        indexes = [
            models.Index(fields=["tenant", "user"]),
            models.Index(fields=["user", "role"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.tenant} ({self.role})"