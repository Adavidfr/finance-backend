from django.conf import settings
from django.db import models

from finances.models import Category


class Budget(models.Model):
    """Límite de gasto mensual (o semanal) para una categoría."""

    class Period(models.TextChoices):
        WEEKLY = "weekly", "Semanal"
        MONTHLY = "monthly", "Mensual"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="budgets")
    limit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    period = models.CharField(max_length=10, choices=Period.choices, default=Period.MONTHLY)
    alert_threshold = models.FloatField(
        default=0.8, help_text="Fracción del límite (0-1) a partir de la cual se dispara la alerta. Ej: 0.8 = 80%"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "category", "period"]

    def __str__(self):
        return f"{self.category.name} - {self.limit_amount} ({self.period})"