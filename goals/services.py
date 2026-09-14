from datetime import date, timedelta


def calculate_goal_projection(goal):
    """
    Calcula el progreso de la meta y, si hay historial de ahorro
    suficiente, proyecta cuándo se cumplirá al ritmo actual.

    Nota: esta versión usa una tasa de ahorro simple basada en el
    tiempo transcurrido desde la creación de la meta. Se puede refinar
    después analizando el historial real de depósitos.
    """
    today = date.today()
    percentage = (
        float(goal.current_amount / goal.target_amount) * 100 if goal.target_amount else 0
    )
    remaining = goal.target_amount - goal.current_amount

    days_elapsed = (today - goal.created_at.date()).days or 1
    daily_rate = float(goal.current_amount) / days_elapsed if days_elapsed > 0 else 0

    projected_days = None
    projected_date = None
    on_track = None

    if daily_rate > 0 and remaining > 0:
        projected_days = int(float(remaining) / daily_rate)
        projected_date = today + timedelta(days=projected_days)

    if goal.target_date:
        on_track = projected_date is None or projected_date <= goal.target_date

    return {
        "percentage": round(percentage, 1),
        "remaining": remaining,
        "projected_date": projected_date,
        "on_track": on_track,
    }