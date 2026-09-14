import re

from .models import CategoryRule

# Palabras muy comunes en descripciones bancarias que NO sirven como
# palabra clave distintiva (no identifican a un comercio específico)
STOPWORDS = {
    "PAGO", "COMPRA", "TRANSFERENCIA", "TRANSACCION", "COBRO", "VENTA",
    "DE", "LA", "EL", "LOS", "LAS", "DEL", "CON", "PARA",
}


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


def extract_keyword(description):
    """
    Busca la palabra más distintiva de una descripción para usarla
    como palabra clave de una regla nueva. Ignora palabras cortas
    (probablemente artículos) y palabras genéricas de banco.
    """
    words = re.findall(r"[A-ZÁÉÍÓÚÑ]{4,}", description.upper())
    candidates = [w for w in words if w not in STOPWORDS]
    if not candidates:
        return None
    # Se queda con la palabra más larga, asumiendo que es la más específica
    return max(candidates, key=len)


def learn_rule_from_correction(transaction):
    """
    Cuando el usuario corrige la categoría de una transacción a mano,
    crea (o actualiza) una CategoryRule personal para que la próxima
    transacción similar se categorice sola.
    """
    if not transaction.category:
        return

    keyword = extract_keyword(transaction.description or transaction.raw_description)
    if not keyword:
        return

    CategoryRule.objects.update_or_create(
        keyword=keyword,
        user=transaction.account.user,
        defaults={"category": transaction.category},
    )