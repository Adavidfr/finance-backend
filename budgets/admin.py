from django.contrib import admin

from .models import Budget


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("category", "user", "limit_amount", "period", "alert_threshold")
    list_filter = ("period",)