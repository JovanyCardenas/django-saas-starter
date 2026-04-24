from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.tenants.models import Tenant, TenantMembership
from apps.rbac.models import Permission, Role, RolePermission, TenantUserRole
from apps.auditlog.models import AuditLogEntry

User = get_user_model()


class RBACCommandTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Org", slug="test-org")
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantMembership.Role.OWNER,
        )

    def test_seed_rbac_creates_permissions_roles_and_audit_log(self):
        call_command("seed_rbac", "test-org")

        self.assertTrue(Permission.objects.exists())
        self.assertTrue(Role.objects.filter(tenant=self.tenant).exists())
        self.assertTrue(RolePermission.objects.filter(role__tenant=self.tenant).exists())

        self.assertTrue(
            AuditLogEntry.objects.filter(
                tenant=self.tenant,
                message__icontains="Seeded RBAC",
            ).exists()
        )

    def test_assign_role_creates_tenant_user_role_and_audit_log(self):
        call_command("seed_rbac", "test-org")
        call_command("assign_role", "test-org", "owner@example.com", "staff_admin", "--replace")

        self.assertTrue(
            TenantUserRole.objects.filter(
                tenant=self.tenant,
                user=self.user,
                role__code="staff_admin",
            ).exists()
        )

        self.assertTrue(
            AuditLogEntry.objects.filter(
                tenant=self.tenant,
                message__icontains="RBAC role",
            ).exists()
        )