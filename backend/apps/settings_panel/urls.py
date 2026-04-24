from django.urls import path
from . import views

app_name = "settings_panel"

urlpatterns = [
    path("organization/", views.organization_settings, name="organization"),
    path("members/", views.member_settings, name="members"),
    path("roles/", views.role_settings, name="roles"),
    path("roles/assign/", views.assign_rbac_role, name="assign_rbac_role"),
    path("roles/<uuid:assignment_id>/deactivate/", views.deactivate_rbac_role, name="deactivate_rbac_role"),
    path("members/add/", views.add_member, name="add_member"),
    path("members/<uuid:membership_id>/role/", views.update_member_role, name="update_member_role"),
    path("members/<uuid:membership_id>/deactivate/", views.deactivate_member, name="deactivate_member"),
    path("members/invite/", views.invite_member, name="invite_member"),
    path("invitations/<uuid:token>/accept/", views.accept_invitation, name="accept_invitation"),
]