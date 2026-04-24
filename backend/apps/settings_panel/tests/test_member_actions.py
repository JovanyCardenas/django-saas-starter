from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.auditlog.models import AuditLogEntry
from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()


class MemberActionTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Org", slug="test-org")

        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
            is_staff=True,
        )

        self.member_user = User.objects.create_user(
            email="member@example.com",
            password="testpass123",
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

    def test_add_member_creates_membership_and_audit_log(self):
        self._login_and_select_tenant()

        response = self.client.post(reverse("settings_panel:add_member"), {
            "email": "member@example.com",
            "role": "member",
        })

        self.assertEqual(response.status_code, 302)

        membership = TenantMembership.objects.get(
            tenant=self.tenant,
            user=self.member_user,
        )
        self.assertEqual(membership.role, "member")
        self.assertTrue(membership.is_active)

        self.assertTrue(
            AuditLogEntry.objects.filter(
                tenant=self.tenant,
                message__icontains="Member",
            ).exists()
        )

    def test_update_member_role(self):
        self._login_and_select_tenant()

        membership = TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.member_user,
            role="member",
            is_active=True,
        )

        response = self.client.post(
            reverse("settings_panel:update_member_role", args=[membership.id]),
            {"role": "staff"},
        )

        self.assertEqual(response.status_code, 302)

        membership.refresh_from_db()
        self.assertEqual(membership.role, "staff")

        self.assertTrue(
            AuditLogEntry.objects.filter(
                tenant=self.tenant,
                message__icontains="Member role updated",
            ).exists()
        )

    def test_deactivate_member(self):
        self._login_and_select_tenant()

        membership = TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.member_user,
            role="member",
            is_active=True,
        )

        response = self.client.post(
            reverse("settings_panel:deactivate_member", args=[membership.id])
        )

        self.assertEqual(response.status_code, 302)

        membership.refresh_from_db()
        self.assertFalse(membership.is_active)

        self.assertTrue(
            AuditLogEntry.objects.filter(
                tenant=self.tenant,
                message__icontains="Member deactivated",
            ).exists()
        )