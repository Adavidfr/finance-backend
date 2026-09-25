from .calculators import calculate_spending_changes
from .llm_service import generate_insight_text
from .models import Insight


def generate_spending_insights(user):
    """
    Calcula los cambios de gasto significativos del usuario, redacta
    cada uno con el LLM, y los guarda como Insight. Si ya existe un
    insight para la misma categoría y mes, lo ACTUALIZA en vez de
    crear uno duplicado. Devuelve la lista de Insights (nuevos o
    actualizados).
    """
    changes = calculate_spending_changes(user)
    result_insights = []

    for change in changes:
        text = generate_insight_text(change)
        insight, _created = Insight.objects.update_or_create(
            user=user,
            insight_type=Insight.InsightType.SPENDING_CHANGE,
            supporting_data__category=change["category"],
            supporting_data__month=change["month"],
            defaults={
                "generated_text": text,
                "supporting_data": change,
            },
        )
        result_insights.append(insight)

    return result_insights