from .models import CategoryRule


def categorize_by_rules(transaction):
    """
    Busca coincidencias de palabras clave en la descripción de la transacción.
    Devuelve la Category encontrada, o None si ninguna regla coincide.

    Prioriza reglas del usuario sobre las globales (is user-specific primero).
    """
    text = f"{transaction.description} {transaction.raw_description}".upper()

    # Reglas del usuario dueño de la cuenta, luego reglas globales
    user = transaction.account.user
    rules = CategoryRule.objects.filter(user=user).select_related("category")
    global_rules = CategoryRule.objects.filter(user__isnull=True).select_related("category")

    for rule_set in (rules, global_rules):
        for rule in rule_set:
            if rule.keyword.upper() in text:
                return rule.category

    return None