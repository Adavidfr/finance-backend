from celery import shared_task

from finances.models import Transaction

from .llm_service import categorize_with_llm
from .services import categorize_by_rules


@shared_task
def categorize_transaction_task(transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id)
    except Transaction.DoesNotExist:
        return f"Transaction {transaction_id} no existe"

    if transaction.categorization_method == Transaction.CategorizationMethod.MANUAL:
        return f"Transaction {transaction_id} ya categorizada manualmente, se omite"

    # Capa 1: reglas
    category = categorize_by_rules(transaction)
    if category:
        transaction.category = category
        transaction.categorization_method = Transaction.CategorizationMethod.RULE
        transaction.categorization_confidence = 1.0
        transaction.save(update_fields=["category", "categorization_method", "categorization_confidence"])
        return f"Transaction {transaction_id} categorizada como '{category.name}' por regla"

    # Capa 2: fallback LLM
    category, confidence = categorize_with_llm(transaction)
    if category:
        transaction.category = category
        transaction.categorization_method = Transaction.CategorizationMethod.LLM
        transaction.categorization_confidence = confidence
        transaction.save(update_fields=["category", "categorization_method", "categorization_confidence"])
        return f"Transaction {transaction_id} categorizada como '{category.name}' por LLM (confianza: {confidence})"

    return f"Transaction {transaction_id} sin categorizar (ni reglas ni LLM tuvieron éxito)"