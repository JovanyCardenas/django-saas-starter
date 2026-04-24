from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.auditlog.models import AuditLogEntry
from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()


class OrganizationSettingsTests(TestCase):
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

    def test_update_organization_settings(self):
        self._login_and_select_tenant()

        response = self.client.post(reverse("settings_panel:organization"), {
            "name": "Updated Test Org",
            "is_active": "on",
        })

        self.assertEqual(response.status_code, 302)

        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.name, "Updated Test Org")
        self.assertTrue(self.tenant.is_active)

        self.assertTrue(
            AuditLogEntry.objects.filter(
                tenant=self.tenant,
                message__icontains="Organization settings updated",
            ).exists()
        )