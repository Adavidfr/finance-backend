from goals.models import SavingsGoal
from goals.services import calculate_goal_projection

MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _format_date_es(date_obj):
    """Convierte una fecha a formato legible en español: '12 de enero de 2027'."""
    return f"{date_obj.day} de {MESES_ES[date_obj.month - 1]} de {date_obj.year}"


def calculate_goal_insights(user):
    """
    Para cada meta de ahorro del usuario, arma los datos de proyección
    listos para redactar. Solo incluye metas que tengan suficiente
    información para decir algo útil (con fecha objetivo, o con
    progreso ya calculado).
    """
    goals_data = []

    for goal in SavingsGoal.objects.filter(user=user):
        projection = calculate_goal_projection(goal)

        # Sin progreso real todavía (0% y sin proyección), no hay nada útil que decir
        if projection["percentage"] == 0 and not projection["projected_date"]:
            continue

        goals_data.append(
            {
                "goal_name": goal.name,
                "goal_id": goal.id,
                "target_amount": float(goal.target_amount),
                "current_amount": float(goal.current_amount),
                "percentage": projection["percentage"],
                "target_date": goal.target_date.isoformat() if goal.target_date else None,
                "projected_date": (
                    projection["projected_date"].isoformat() if projection["projected_date"] else None
                ),
                "projected_date_readable": (
                    _format_date_es(projection["projected_date"])
                    if projection["projected_date"]
                    else None
                ),
                "on_track": projection["on_track"],
            }
        )

    return goals_data