from django.urls import path
from . import views

app_name = "settings_panel"

urlpatterns = [
    path("organization/", views.organization_settings, name="organization"),
    path("members/", views.member_settings, name="members"),
    path("roles/", views.role_settings, name="roles"),
]