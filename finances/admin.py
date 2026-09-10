from django.contrib import admin

from .models import Account, Category, Transaction


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "account_type", "balance", "currency")
    list_filter = ("account_type", "currency")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category_type", "parent", "is_default")
    list_filter = ("category_type", "is_default")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("description", "amount", "date", "account", "category", "categorization_method")
    list_filter = ("categorization_method", "source")
    search_fields = ("description",)