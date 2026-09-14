from .calculators import calculate_spending_changes
from .llm_service import generate_insight_text
from .models import Insight


def generate_spending_insights(user):
    """
    Calcula los cambios de gasto significativos del usuario, redacta
    cada uno con el LLM, y los guarda como Insight. Devuelve la lista
    de Insights creados.
    """
    changes = calculate_spending_changes(user)
    created_insights = []

    for change in changes:
        text = generate_insight_text(change)
        insight = Insight.objects.create(
            user=user,
            insight_type=Insight.InsightType.SPENDING_CHANGE,
            generated_text=text,
            supporting_data=change,
        )
        created_insights.append(insight)

    return created_insights