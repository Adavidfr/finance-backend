from django.contrib import admin

from .models import Insight


@admin.register(Insight)
class InsightAdmin(admin.ModelAdmin):
    list_display = ("insight_type", "user", "generated_text", "created_at")
    list_filter = ("insight_type",)