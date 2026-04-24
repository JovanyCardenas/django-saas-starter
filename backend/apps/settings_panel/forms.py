from django import forms
from apps.tenants.models import TenantMembership

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