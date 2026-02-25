from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from apps.tenants.middleware import get_current_tenant
from .utils import get_user_role_for_tenant


def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("accounts:login")

            tenant = get_current_tenant(request)
            if not tenant:
                return HttpResponseForbidden("No tenant selected.")

            role = get_user_role_for_tenant(request.user, tenant)

            if role not in allowed_roles:
                return HttpResponseForbidden("You do not have permission.")

            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator