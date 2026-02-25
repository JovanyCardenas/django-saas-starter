from django.contrib import admin
from .models import Permission, Role, RolePermission, TenantUserRole


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "created_at")
    search_fields = ("code", "name")
    ordering = ("code",)


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 0
    autocomplete_fields = ("permission",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("tenant", "code", "name", "is_active", "created_at")
    search_fields = ("tenant__name", "tenant__slug", "code", "name")
    list_filter = ("tenant", "is_active")
    ordering = ("tenant__name", "code")
    inlines = [RolePermissionInline]


@admin.register(TenantUserRole)
class TenantUserRoleAdmin(admin.ModelAdmin):
    list_display = ("tenant", "user", "role", "is_active", "assigned_at")
    search_fields = ("tenant__name", "tenant__slug", "user__email", "role__code", "role__name")
    list_filter = ("tenant", "is_active", "role__code")
    ordering = ("tenant__name", "user")
    autocomplete_fields = ("tenant", "user", "role")