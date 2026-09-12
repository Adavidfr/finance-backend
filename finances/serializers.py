from rest_framework import serializers

from .models import Account, Category, Transaction


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            "id",
            "name",
            "account_type",
            "currency",
            "balance",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "category_type",
            "parent",
            "icon",
            "color",
            "is_default",
        ]
        read_only_fields = ["id", "is_default"]


class TransactionSerializer(serializers.ModelSerializer):
    # Al leer (GET), mostramos el nombre de la categoría, no solo el ID
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "account",
            "category",
            "category_name",
            "amount",
            "date",
            "description",
            "raw_description",
            "source",
            "categorization_method",
            "categorization_confidence",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "categorization_method",
            "categorization_confidence",
            "created_at",
        ]