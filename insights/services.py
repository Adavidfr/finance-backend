from .budget_calculators import calculate_budget_insights
from .calculators import calculate_spending_changes
from .goal_calculators import calculate_goal_insights
from .llm_service import (
    generate_budget_insight_text,
    generate_goal_insight_text,
    generate_insight_text,
)
from .models import Insight


def generate_spending_insights(user):
    """Calcula y redacta insights de cambios de gasto por categoría."""
    changes = calculate_spending_changes(user)
    result = []

    for change in changes:
        text = generate_insight_text(change)
        insight, _created = Insight.objects.update_or_create(
            user=user,
            insight_type=Insight.InsightType.SPENDING_CHANGE,
            supporting_data__category=change["category"],
            supporting_data__month=change["month"],
            defaults={"generated_text": text, "supporting_data": change},
        )
        result.append(insight)

    return result


def generate_goal_insights(user):
    """Calcula y redacta insights de proyección de metas de ahorro."""
    goals_data = calculate_goal_insights(user)
    result = []

    for goal_data in goals_data:
        text = generate_goal_insight_text(goal_data)
        insight, _created = Insight.objects.update_or_create(
            user=user,
            insight_type=Insight.InsightType.GOAL_PROJECTION,
            supporting_data__goal_id=goal_data["goal_id"],
            defaults={"generated_text": text, "supporting_data": goal_data},
        )
        result.append(insight)

    return result


def generate_budget_insights(user):
    """Calcula y redacta insights de alerta de presupuestos cerca del límite."""
    budgets_data = calculate_budget_insights(user)
    result = []

    for budget_data in budgets_data:
        text = generate_budget_insight_text(budget_data)
        insight, _created = Insight.objects.update_or_create(
            user=user,
            insight_type=Insight.InsightType.BUDGET_ALERT,
            supporting_data__budget_id=budget_data["budget_id"],
            defaults={"generated_text": text, "supporting_data": budget_data},
        )
        result.append(insight)

    return result


def generate_all_insights(user):
    """Genera los tres tipos de insight de una vez."""
    return (
        generate_spending_insights(user)
        + generate_goal_insights(user)
        + generate_budget_insights(user)
    )