import logging

from django.conf import settings
from google import genai

logger = logging.getLogger(__name__)


def generate_insight_text(spending_change):
    """
    Recibe un diccionario YA CALCULADO (categoría, montos, % de cambio)
    y le pide a Gemini que lo redacte como una frase natural.

    El LLM NUNCA calcula números — solo redacta a partir de datos exactos
    que ya vienen resueltos por Django. Esto evita que la IA "invente"
    o redondee mal una cifra financiera.
    """
    if not settings.GEMINI_API_KEY:
        return _fallback_text(spending_change)

    direction = "aumentaron" if spending_change["pct_change"] > 0 else "disminuyeron"

    prompt = f"""Redacta UNA sola frase corta y natural en español, para un dashboard financiero personal,
que informe este dato exacto al usuario. No inventes ni cambies ningún número.

Categoría: {spending_change['category']}
Gasto este mes: ${spending_change['current']:.2f}
Gasto mes anterior: ${spending_change['previous']:.2f}
Cambio: {abs(spending_change['pct_change'])}% ({direction})

Responde ÚNICAMENTE con la frase, sin comillas, sin explicaciones adicionales."""

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )
        return response.text.strip()
    except Exception:
        logger.exception("Error generando texto de insight con Gemini")
        return _fallback_text(spending_change)


def _fallback_text(spending_change):
    """
    Si Gemini falla o no hay API key, generamos una frase simple
    con una plantilla fija — el insight sigue siendo útil, solo
    menos "natural" en la redacción.
    """
    direction = "aumentaron" if spending_change["pct_change"] > 0 else "disminuyeron"
    return (
        f"Tus gastos en {spending_change['category']} {direction} "
        f"{abs(spending_change['pct_change'])}% este mes "
        f"(${spending_change['previous']:.2f} → ${spending_change['current']:.2f})."
    )