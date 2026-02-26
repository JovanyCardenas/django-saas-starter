from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class AuditLogEntry(models.Model):
    """Tenant-scoped audit log entry (generic)."""

    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        ACCESS = "access", "Access"
        SYSTEM = "system", "System"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="audit_entries",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_entries",
    )

    actor_email = models.EmailField(blank=True, default="")

    action = models.CharField(max_length=32, choices=Action.choices, default=Action.SYSTEM)
    message = models.TextField(blank=True, default="")

    object_type = models.CharField(max_length=120, blank=True, default="")
    object_id = models.UUIDField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, default="")

    meta = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "-created_at"]),
            models.Index(fields=["tenant", "action"]),
            models.Index(fields=["object_type", "object_id"]),
        ]

    def __str__(self) -> str:
        who = self.actor_email or (str(self.actor) if self.actor else "system")
        return f"{self.action} by {who} ({self.created_at})"