from rest_framework import serializers

from .models import Budget
from .services import calculate_budget_progress


class BudgetSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = [
            "id",
            "category",
            "limit_amount",
            "period",
            "alert_threshold",
            "progress",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_progress(self, obj):
        return calculate_budget_progress(obj)