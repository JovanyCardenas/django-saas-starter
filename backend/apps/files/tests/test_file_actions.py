from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.auditlog.models import AuditLogEntry
from apps.files.models import FileAsset
from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()


class FileActionTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Org", slug="test-org")

        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
            is_staff=True,
        )

        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.owner,
            role=TenantMembership.Role.OWNER,
            is_active=True,
        )

    def _login_and_select_tenant(self):
        self.client.login(email="owner@example.com", password="testpass123")
        session = self.client.session
        session["active_tenant_id"] = str(self.tenant.id)
        session.save()

    def test_upload_file_creates_file_and_audit_log(self):
        self._login_and_select_tenant()

        uploaded = SimpleUploadedFile(
            "test.txt",
            b"hello world",
            content_type="text/plain",
        )

        response = self.client.post(reverse("files:upload"), {
            "title": "Test File",
            "category": "document",
            "description": "Test description",
            "file": uploaded,
        })

        self.assertEqual(response.status_code, 302)

        file_asset = FileAsset.objects.get(title="Test File")
        self.assertEqual(file_asset.tenant, self.tenant)
        self.assertEqual(file_asset.uploaded_by, self.owner)
        self.assertTrue(file_asset.is_active)

        self.assertTrue(
            AuditLogEntry.objects.filter(
                tenant=self.tenant,
                message__icontains="File uploaded",
            ).exists()
        )

    def test_deactivate_file_updates_file_and_audit_log(self):
        self._login_and_select_tenant()

        uploaded = SimpleUploadedFile(
            "test.txt",
            b"hello world",
            content_type="text/plain",
        )

        file_asset = FileAsset.objects.create(
            tenant=self.tenant,
            uploaded_by=self.owner,
            title="Test File",
            file=uploaded,
            category="document",
            description="Test description",
        )

        response = self.client.post(reverse("files:deactivate", args=[file_asset.id]))

        self.assertEqual(response.status_code, 302)

        file_asset.refresh_from_db()
        self.assertFalse(file_asset.is_active)

        self.assertTrue(
            AuditLogEntry.objects.filter(
                tenant=self.tenant,
                message__icontains="File deactivated",
            ).exists()
        )