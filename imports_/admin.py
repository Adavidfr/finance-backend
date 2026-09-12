from django.contrib import admin

from .models import ImportJob


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "account", "status", "total_rows", "processed_rows", "created_at")
    list_filter = ("status",)