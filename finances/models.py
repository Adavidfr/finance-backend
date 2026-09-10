from django.conf import settings
from django.db import models


class Account(models.Model):
    """Una cuenta bancaria o de efectivo del usuario."""

    class AccountType(models.TextChoices):
        CHECKING = "checking", "Cuenta corriente"
        SAVINGS = "savings", "Ahorros"
        CREDIT = "credit", "Tarjeta de crédito"
        CASH = "cash", "Efectivo"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accounts"
    )
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=AccountType.choices)
    currency = models.CharField(max_length=3, default="USD")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user})"


class Category(models.Model):
    """Categoría de transacción. Puede tener subcategorías (parent)."""

    class CategoryType(models.TextChoices):
        INCOME = "income", "Ingreso"
        EXPENSE = "expense", "Gasto"

    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=10, choices=CategoryType.choices)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="subcategories"
    )
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, blank=True)  # ej: "#FF5733"
    is_default = models.BooleanField(default=False)  # categorías del sistema vs. creadas por el usuario
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="categories"
    )

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Transaction(models.Model):
    """Un movimiento de dinero (ingreso o gasto)."""

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        IMPORT = "import", "Importado (CSV)"

    class CategorizationMethod(models.TextChoices):
        RULE = "rule", "Regla"
        LLM = "llm", "IA (LLM)"
        MANUAL = "manual", "Manual"
        PENDING = "pending", "Pendiente"

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions")
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="transactions"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.CharField(max_length=255)
    raw_description = models.CharField(max_length=255, blank=True)  # texto original del CSV, sin limpiar
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.MANUAL)
    categorization_method = models.CharField(
        max_length=10, choices=CategorizationMethod.choices, default=CategorizationMethod.PENDING
    )
    categorization_confidence = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.description} ({self.amount})"