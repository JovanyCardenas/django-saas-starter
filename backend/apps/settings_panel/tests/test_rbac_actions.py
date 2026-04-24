from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.auditlog.models import AuditLogEntry
from apps.rbac.models import Role, TenantUserRole
from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()


class RBACActionTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Org", slug="test-org")

        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
            is_staff=True,
        )

        self.target_user = User.objects.create_user(
            email="target@example.com",
            password="testpass123",
        )

        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.owner,
            role=TenantMembership.Role.OWNER,
            is_active=True,
        )

        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.target_user,
            role=TenantMembership.Role.MEMBER,
            is_active=True,
        )

        self.role = Role.objects.create(
            tenant=self.tenant,
            code="staff_admin",
            name="Staff Admin",
            is_active=True,
        )

    def _login_and_select_tenant(self):
        self.client.login(email="owner@example.com", password="testpass123")
        session = self.client.session
        session["active_tenant_id"] = str(self.tenant.id)
        session.save()

    def test_assign_rbac_role_creates_assignment_and_audit_log(self):
        self._login_and_select_tenant()

        response = self.client.post(reverse("settings_panel:assign_rbac_role"), {
            "user_email": "target@example.com",
            "role_id": str(self.role.id),
        })

        self.assertEqual(response.status_code, 302)

        assignment = TenantUserRole.objects.get(
            tenant=self.tenant,
            user=self.target_user,
        )

        self.assertEqual(assignment.role, self.role)
        self.assertTrue(assignment.is_active)

        self.assertTrue(
            AuditLogEntry.objects.filter(
                tenant=self.tenant,
                message__icontains="RBAC role",
            ).exists()
        )

    def test_deactivate_rbac_role_assignment(self):
        self._login_and_select_tenant()

        assignment = TenantUserRole.objects.create(
            tenant=self.tenant,
            user=self.target_user,
            role=self.role,
            is_active=True,
        )

        response = self.client.post(
            reverse("settings_panel:deactivate_rbac_role", args=[assignment.id])
        )

        self.assertEqual(response.status_code, 302)

        assignment.refresh_from_db()
        self.assertFalse(assignment.is_active)

        self.assertTrue(
            AuditLogEntry.objects.filter(
                tenant=self.tenant,
                message__icontains="RBAC role deactivated",
            ).exists()
        )