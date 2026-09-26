from budgets.models import Budget
from budgets.services import calculate_budget_progress


def calculate_budget_insights(user):
    """
    Para cada presupuesto activo, arma los datos de progreso listos
    para redactar. Solo incluye los que están cerca o por encima del
    umbral de alerta — un presupuesto sano al 20% no necesita un insight.
    """
    budgets_data = []

    for budget in Budget.objects.filter(user=user):
        progress = calculate_budget_progress(budget)

        if not progress["is_alert"]:
            continue

        budgets_data.append(
            {
                "budget_id": budget.id,
                "category": budget.category.name,
                "spent": float(progress["spent"]),
                "limit": float(progress["limit"]),
                "percentage": progress["percentage"],
                "period": budget.period,
            }
        )

    return budgets_data