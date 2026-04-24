from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()


class SettingsPanelViewTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Org", slug="test-org")

        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
            is_staff=True,
        )

        self.viewer = User.objects.create_user(
            email="viewer@example.com",
            password="testpass123",
        )

        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.owner,
            role=TenantMembership.Role.OWNER,
        )

        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.viewer,
            role=TenantMembership.Role.VIEWER,
        )

    def _select_tenant(self):
        session = self.client.session
        session["active_tenant_id"] = str(self.tenant.id)
        session.save()

    def test_organization_settings_requires_login(self):
        response = self.client.get(reverse("settings_panel:organization"))
        self.assertEqual(response.status_code, 302)

    def test_owner_can_view_organization_settings(self):
        self.client.login(email="owner@example.com", password="testpass123")
        self._select_tenant()

        response = self.client.get(reverse("settings_panel:organization"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Org")

    def test_viewer_cannot_view_organization_settings(self):
        self.client.login(email="viewer@example.com", password="testpass123")
        self._select_tenant()

        response = self.client.get(reverse("settings_panel:organization"))
        self.assertEqual(response.status_code, 403)