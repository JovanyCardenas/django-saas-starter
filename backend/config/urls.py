from django.contrib import admin
from django.urls import path, include

from django.http import HttpResponse

def home(request):
    return HttpResponse("Home (replace with dashboard)")

urlpatterns = [
    path("admin/", admin.site.urls),

    path("accounts/", include("apps.accounts.urls")),
    path("tenants/", include("apps.tenants.urls")),

    path("", include("apps.dashboard.urls")),
]