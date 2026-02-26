from django.urls import path
from .views import audit_home

app_name = "auditlog"

urlpatterns = [
    path("", audit_home, name="home"),
]