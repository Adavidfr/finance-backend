from rest_framework import serializers

from .models import Insight


class InsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insight
        fields = ["id", "insight_type", "generated_text", "supporting_data", "created_at"]
        read_only_fields = fields