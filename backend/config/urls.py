from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.http import HttpResponse

handler403 = "config.views.custom_403"
handler404 = "config.views.custom_404"

urlpatterns = [
    path("admin/", admin.site.urls),

    path("accounts/", include("apps.accounts.urls")),
    path("tenants/", include("apps.tenants.urls")),
    path("audit/", include("apps.auditlog.urls")),
    path("settings/", include("apps.settings_panel.urls")),
    path("files/", include("apps.files.urls")),
    path("", include("apps.dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)