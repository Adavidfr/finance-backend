from rest_framework import serializers

from .models import SavingsGoal
from .services import calculate_goal_projection


class SavingsGoalSerializer(serializers.ModelSerializer):
    projection = serializers.SerializerMethodField()

    class Meta:
        model = SavingsGoal
        fields = [
            "id",
            "name",
            "target_amount",
            "current_amount",
            "target_date",
            "projection",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_projection(self, obj):
        return calculate_goal_projection(obj)