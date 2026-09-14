import json
import logging

from django.conf import settings
from google import genai
from google.genai import types

from finances.models import Category

logger = logging.getLogger(__name__)


def _get_client():
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def categorize_with_llm(transaction):
    """
    Le pide a Gemini que elija la categoría más apropiada para la
    transacción, de entre las categorías existentes del usuario.

    Devuelve (Category, confidence) o (None, 0.0) si falla o no hay
    API key configurada.
    """
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY no configurada, se omite el fallback LLM")
        return None, 0.0

    user = transaction.account.user
    categories = Category.objects.filter(
        category_type=Category.CategoryType.EXPENSE if transaction.amount < 0 else Category.CategoryType.INCOME
    ).filter(models_q_user_or_none(user))

    category_names = list(categories.values_list("name", flat=True))
    if not category_names:
        return None, 0.0

    prompt = f"""Eres un clasificador de transacciones financieras.
Dada la siguiente descripción de una transacción bancaria, elige la categoría MÁS apropiada
de esta lista exacta: {category_names}

Descripción: "{transaction.description}"
Monto: {transaction.amount}

Responde ÚNICAMENTE con un JSON válido, sin texto adicional, con este formato exacto:
{{"category": "nombre_exacto_de_la_lista", "confidence": 0.0}}

confidence debe ser un número entre 0 y 1 que represente qué tan seguro estás."""

    try:
        client = _get_client()
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        result = json.loads(response.text)
        category_name = result.get("category")
        confidence = float(result.get("confidence", 0.5))

        category = categories.filter(name=category_name).first()
        if category:
            return category, confidence

        logger.warning("Gemini devolvió una categoría no reconocida: %s", category_name)
        return None, 0.0

    except Exception:
        logger.exception("Error llamando a Gemini para categorizar transaction %s", transaction.id)
        return None, 0.0


def models_q_user_or_none(user):
    from django.db.models import Q
    return Q(user=user) | Q(user__isnull=True)