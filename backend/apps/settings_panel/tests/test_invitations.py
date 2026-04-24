from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.auditlog.models import AuditLogEntry
from apps.settings_panel.models import TenantInvitation
from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()


class InvitationTests(TestCase):
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

    def test_invite_member_creates_invitation_and_audit_log(self):
        self._login_and_select_tenant()

        response = self.client.post(reverse("settings_panel:invite_member"), {
            "email": "newuser@example.com",
            "role": "member",
        })

        self.assertEqual(response.status_code, 302)

        invitation = TenantInvitation.objects.get(email="newuser@example.com")
        self.assertEqual(invitation.tenant, self.tenant)
        self.assertEqual(invitation.role, "member")
        self.assertEqual(invitation.status, TenantInvitation.Status.PENDING)

        self.assertTrue(
            AuditLogEntry.objects.filter(
                tenant=self.tenant,
                message__icontains="Invitation sent",
            ).exists()
        )

    def test_accept_invitation_creates_user_membership_and_audit_log(self):
        invitation = TenantInvitation.objects.create(
            tenant=self.tenant,
            email="newuser@example.com",
            role="member",
            invited_by=self.owner,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )

        response = self.client.post(
            reverse("settings_panel:accept_invitation", args=[invitation.token]),
            {
                "password1": "newpass123",
                "password2": "newpass123",
            },
        )

        self.assertEqual(response.status_code, 302)

        user = User.objects.get(email="newuser@example.com")
        membership = TenantMembership.objects.get(tenant=self.tenant, user=user)

        self.assertEqual(membership.role, "member")
        self.assertTrue(membership.is_active)

        invitation.refresh_from_db()
        self.assertEqual(invitation.status, TenantInvitation.Status.ACCEPTED)
        self.assertEqual(invitation.accepted_by, user)

        self.assertTrue(
            AuditLogEntry.objects.filter(
                tenant=self.tenant,
                message__icontains="Invitation accepted",
            ).exists()
        )