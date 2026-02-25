from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.tenants.utils import require_tenant

@login_required
@require_tenant
def home(request):
    return render(request, "dashboard/home.html", {"tenant": request.tenant})