from django.contrib import admin

from .models import CategoryRule


@admin.register(CategoryRule)
class CategoryRuleAdmin(admin.ModelAdmin):
    list_display = ("keyword", "category", "user")
    list_filter = ("category",)
    search_fields = ("keyword",)