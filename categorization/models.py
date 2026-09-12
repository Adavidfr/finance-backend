from django.conf import settings
from django.db import models

from finances.models import Category


class CategoryRule(models.Model):
    """
    Relaciona una palabra clave (ej. 'UBER', 'NETFLIX') con una categoría.
    Si 'user' es None, es una regla global del sistema (aplica a todos).
    Si tiene un 'user', es una regla personalizada de ese usuario
    (por ejemplo, creada cuando corrige una categorización manualmente).
    """

    keyword = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="rules")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="category_rules"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["keyword"]

    def __str__(self):
        return f"{self.keyword} → {self.category.name}"