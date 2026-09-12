from celery import shared_task

from finances.models import Transaction

from .services import categorize_by_rules


@shared_task
def categorize_transaction_task(transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id)
    except Transaction.DoesNotExist:
        return f"Transaction {transaction_id} no existe"

    # Si ya tiene categoría asignada manualmente, no la pisamos
    if transaction.categorization_method == Transaction.CategorizationMethod.MANUAL:
        return f"Transaction {transaction_id} ya categorizada manualmente, se omite"

    category = categorize_by_rules(transaction)

    if category:
        transaction.category = category
        transaction.categorization_method = Transaction.CategorizationMethod.RULE
        transaction.categorization_confidence = 1.0
        transaction.save(update_fields=["category", "categorization_method", "categorization_confidence"])
        return f"Transaction {transaction_id} categorizada como '{category.name}' por regla"

    # Ninguna regla coincidió — queda pendiente para el fallback LLM (lo haremos después)
    return f"Transaction {transaction_id} sin coincidencia de reglas, queda pendiente"