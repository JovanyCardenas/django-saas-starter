from django import forms
from apps.tenants.models import TenantMembership, Tenant

from apps.rbac.models import Role


class AssignRBACRoleForm(forms.Form):
    user_email = forms.EmailField()
    role_id = forms.UUIDField()

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tenant = tenant

    def clean_role_id(self):
        role_id = self.cleaned_data["role_id"]
        if not Role.objects.filter(id=role_id, tenant=self.tenant, is_active=True).exists():
            raise forms.ValidationError("Invalid role for this tenant.")
        return role_id

class AddMemberForm(forms.Form):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=TenantMembership.Role.choices)


class UpdateMemberRoleForm(forms.Form):
    role = forms.ChoiceField(choices=TenantMembership.Role.choices)

class InviteMemberForm(forms.Form):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=TenantMembership.Role.choices)

class AcceptInvitationForm(forms.Form):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class OrganizationSettingsForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ["name", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "rounded-md border px-3 py-2 text-sm",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "h-4 w-4 rounded border-gray-300",
            }),
        }