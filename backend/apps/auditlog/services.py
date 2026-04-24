from django.urls import path
from .views import audit_home

app_name = "auditlog"

urlpatterns = [
    path("", audit_home, name="home"),
]

def log_event(*, tenant, action, message="", actor=None, actor_email="", request=None, object_type="", object_id="", meta=None):
    from .models import AuditLogEntry

    ip = None
    user_agent = ""

    if request:
        ip = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")

    return AuditLogEntry.objects.create(
        tenant=tenant,
        actor=actor,
        actor_email=actor_email or getattr(actor, "email", ""),
        action=action,
        message=message,
        object_type=object_type,
        object_id=object_id or None,
        ip_address=ip,
        user_agent=user_agent[:255],
        meta=meta or {},
    )