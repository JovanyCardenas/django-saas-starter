from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.tenants.models import Tenant, TenantMembership
from apps.auditlog.models import AuditLogEntry

User = get_user_model()


class TenantCommandTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
        )

    def test_create_tenant_command_creates_tenant_and_audit_log(self):
        call_command("create_tenant", "Test Org", "--slug", "test-org")

        tenant = Tenant.objects.get(slug="test-org")
        self.assertEqual(tenant.name, "Test Org")

        self.assertTrue(
            AuditLogEntry.objects.filter(
                tenant=tenant,
                message__icontains="Tenant created",
            ).exists()
        )

    def test_add_membership_command_creates_membership_and_audit_log(self):
        tenant = Tenant.objects.create(name="Test Org", slug="test-org")

        call_command("add_membership", "test-org", "owner@example.com", "--role", "owner")

        membership = TenantMembership.objects.get(tenant=tenant, user=self.user)
        self.assertEqual(membership.role, TenantMembership.Role.OWNER)

        self.assertTrue(
            AuditLogEntry.objects.filter(
                tenant=tenant,
                message__icontains="Tenant membership created",
            ).exists()
        )