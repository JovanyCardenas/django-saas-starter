from django.contrib import admin
from .models import FileAsset


@admin.register(FileAsset)
class FileAssetAdmin(admin.ModelAdmin):
    list_display = ("title", "tenant", "category", "uploaded_by", "is_active", "uploaded_at")
    list_filter = ("tenant", "category", "is_active")
    search_fields = ("title", "description", "uploaded_by__email")
    readonly_fields = ("id", "uploaded_at")