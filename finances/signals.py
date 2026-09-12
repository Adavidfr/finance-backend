from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Transaction


@receiver(post_save, sender=Transaction)
def trigger_categorization(sender, instance, created, **kwargs):
    """
    Cada vez que se crea una Transaction nueva (created=True),
    dispara la categorización en segundo plano vía Celery.
    """
    if created and instance.categorization_method == Transaction.CategorizationMethod.PENDING:
        from categorization.tasks import categorize_transaction_task
        categorize_transaction_task.delay(instance.id)