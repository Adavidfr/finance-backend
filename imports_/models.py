from django.conf import settings
from django.db import models

from finances.models import Account


class ImportJob(models.Model):
    """Registro de una carga de CSV: qué archivo, quién lo subió, en qué estado va."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        PROCESSING = "processing", "Procesando"
        DONE = "done", "Completado"
        FAILED = "failed", "Falló"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="import_jobs")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="import_jobs")
    file = models.FileField(upload_to="imports/%Y/%m/")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Import {self.id} ({self.status})"