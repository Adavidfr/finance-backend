from datetime import date, timedelta

from django.db.models import Sum

from finances.models import Transaction


def get_period_range(period):
    """Devuelve (fecha_inicio, fecha_fin) del período actual."""
    today = date.today()
    if period == "weekly":
        start = today - timedelta(days=today.weekday())  # lunes de esta semana
        end = today
    else:  # monthly
        start = today.replace(day=1)
        end = today
    return start, end


def calculate_budget_progress(budget):
    """
    Calcula cuánto se ha gastado en la categoría del budget durante
    el período actual, y si ya se pasó del umbral de alerta.
    """
    start, end = get_period_range(budget.period)

    spent = Transaction.objects.filter(
        account__user=budget.user,
        category=budget.category,
        date__gte=start,
        date__lte=end,
        amount__lt=0,
    ).aggregate(total=Sum("amount"))["total"] or 0

    spent = abs(spent)
    percentage = float(spent / budget.limit_amount) if budget.limit_amount else 0
    is_alert = percentage >= budget.alert_threshold

    return {
        "spent": spent,
        "limit": budget.limit_amount,
        "percentage": round(percentage * 100, 1),
        "is_alert": is_alert,
        "remaining": budget.limit_amount - spent,
    }