from django.contrib import admin
from .models import Tenant, TenantMembership


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    search_fields = ("name", "slug")
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ("tenant", "user", "role", "is_active", "joined_at")
    search_fields = ("tenant__name", "user__email", "user__username")
    list_filter = ("role", "is_active", "tenant")
    ordering = ("tenant", "role", "user")

# # Require admin/staff
# from apps.tenants.utils import require_tenant_role
#
# @require_tenant_role("owner", "admin")
# def admin_dashboard(request):
#     ...