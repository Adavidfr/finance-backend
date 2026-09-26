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

    prompt = f"""Redacta una frase en español para un dashboard financiero, usando EXACTAMENTE
esta plantilla, sin desviarte del formato ni agregar nada extra:

"Tus gastos en {{categoria}} {{aumentaron/disminuyeron}} {{porcentaje}}% este mes (${{monto_anterior}} → ${{monto_actual}})."

Datos exactos a usar (no los cambies, no los redondees distinto):
- categoria: {spending_change['category']}
- dirección: {direction}
- porcentaje: {abs(spending_change['pct_change'])}
- monto_anterior: {spending_change['previous']:.2f}
- monto_actual: {spending_change['current']:.2f}

Responde ÚNICAMENTE con la frase ya completada, sin comillas, sin explicaciones, sin texto adicional antes o después."""

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

def generate_goal_insight_text(goal_data):
    """Redacta un insight sobre el progreso/proyección de una meta de ahorro."""
    if not settings.GEMINI_API_KEY:
        return _fallback_goal_text(goal_data)

    prompt = f"""Redacta UNA sola frase corta y natural en español sobre el progreso de una
meta de ahorro, para un dashboard financiero. No inventes ni cambies ningún número.

Meta: {goal_data['goal_name']}
Monto objetivo: ${goal_data['target_amount']:.2f}
Ahorrado hasta ahora: ${goal_data['current_amount']:.2f} ({goal_data['percentage']}%)
Fecha proyectada de cumplimiento al ritmo actual: {goal_data['projected_date_readable'] or 'no calculable todavía'}
Fecha objetivo del usuario: {goal_data['target_date'] or 'sin fecha límite definida'}
¿Va a tiempo?: {goal_data['on_track']}

Si hay fecha proyectada, menciónala. Si "on_track" es False, la frase debe transmitir que
va retrasado, sin ser alarmista. Responde ÚNICAMENTE con la frase, sin comillas."""

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )
        return response.text.strip()
    except Exception:
        logger.exception("Error generando texto de insight de meta con Gemini")
        return _fallback_goal_text(goal_data)


def _fallback_goal_text(goal_data):
    if goal_data["projected_date_readable"]:
        return (
            f"Al ritmo actual de ahorro, alcanzarás tu meta '{goal_data['goal_name']}' "
            f"de ${goal_data['target_amount']:.2f} aproximadamente el {goal_data['projected_date_readable']}."
        )
    return (
        f"Llevas {goal_data['percentage']}% de tu meta '{goal_data['goal_name']}' "
        f"(${goal_data['current_amount']:.2f} de ${goal_data['target_amount']:.2f})."
    )


def generate_budget_insight_text(budget_data):
    """Redacta un insight de alerta sobre un presupuesto cerca de su límite."""
    if not settings.GEMINI_API_KEY:
        return _fallback_budget_text(budget_data)

    prompt = f"""Redacta UNA sola frase corta y natural en español alertando sobre un
presupuesto cerca de su límite, para un dashboard financiero. No inventes ni cambies
ningún número. Tono informativo, no alarmista.

Categoría: {budget_data['category']}
Gastado: ${budget_data['spent']:.2f}
Límite: ${budget_data['limit']:.2f} ({budget_data['percentage']}% usado)
Período: {budget_data['period']}

Responde ÚNICAMENTE con la frase, sin comillas."""

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )
        return response.text.strip()
    except Exception:
        logger.exception("Error generando texto de insight de presupuesto con Gemini")
        return _fallback_budget_text(budget_data)


def _fallback_budget_text(budget_data):
    return (
        f"Ya usaste {budget_data['percentage']}% de tu presupuesto de {budget_data['category']} "
        f"(${budget_data['spent']:.2f} de ${budget_data['limit']:.2f})."
    )