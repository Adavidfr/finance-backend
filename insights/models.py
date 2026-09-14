from django.conf import settings
from django.db import models


class Insight(models.Model):
    """Un insight en lenguaje natural, generado a partir de datos reales del usuario."""

    class InsightType(models.TextChoices):
        SPENDING_CHANGE = "spending_change", "Cambio de gasto"
        GOAL_PROJECTION = "goal_projection", "Proyección de meta"
        BUDGET_ALERT = "budget_alert", "Alerta de presupuesto"
        GENERAL = "general", "General"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="insights")
    insight_type = models.CharField(max_length=20, choices=InsightType.choices)
    generated_text = models.TextField()
    supporting_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.insight_type}] {self.generated_text[:60]}"