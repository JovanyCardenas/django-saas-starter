from django import forms
from apps.tenants.models import TenantMembership


class AddMemberForm(forms.Form):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=TenantMembership.Role.choices)


class UpdateMemberRoleForm(forms.Form):
    role = forms.ChoiceField(choices=TenantMembership.Role.choices)