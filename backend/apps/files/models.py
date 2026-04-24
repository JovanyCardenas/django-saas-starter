from __future__ import annotations

import uuid
from django.conf import settings
from django.db import models


def tenant_upload_path(instance, filename):
    tenant_slug = instance.tenant.slug if instance.tenant else "unassigned"
    return f"tenants/{tenant_slug}/files/{filename}"


class FileAsset(models.Model):
    class Category(models.TextChoices):
        GENERAL = "general", "General"
        DOCUMENT = "document", "Document"
        IMAGE = "image", "Image"
        FORM = "form", "Form"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="files",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_files",
    )

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=tenant_upload_path)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.GENERAL)

    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["tenant", "-uploaded_at"]),
            models.Index(fields=["tenant", "category"]),
        ]

    def __str__(self):
        return self.title