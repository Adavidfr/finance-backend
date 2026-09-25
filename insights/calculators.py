from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Sum

from finances.models import Transaction


def get_month_range(months_ago=0):
    """Devuelve (inicio, fin) del mes actual, o de N meses atrás."""
    today = date.today()
    target = today - relativedelta(months=months_ago)
    start = target.replace(day=1)
    end = (start + relativedelta(months=1)) - relativedelta(days=1)
    return start, end


def calculate_spending_changes(user):
    """
    Compara el gasto por categoría de este mes contra el mes anterior.
    Devuelve una lista de cambios significativos (>15% de variación),
    ordenados por el cambio más grande primero.
    """
    this_start, this_end = get_month_range(0)
    prev_start, prev_end = get_month_range(1)

    def spending_by_category(start, end):
        qs = (
            Transaction.objects.filter(
                account__user=user, date__gte=start, date__lte=end, amount__lt=0
            )
            .values("category__name")
            .annotate(total=Sum("amount"))
        )
        return {row["category__name"]: abs(row["total"]) for row in qs if row["category__name"]}

    current = spending_by_category(this_start, this_end)
    previous = spending_by_category(prev_start, prev_end)

    changes = []
    for category, current_amount in current.items():
        previous_amount = previous.get(category, Decimal("0"))
        if previous_amount == 0:
            continue  # categoría nueva este mes, no hay base de comparación
        pct_change = float((current_amount - previous_amount) / previous_amount * 100)
        if abs(pct_change) >= 15:
            changes.append(
                {
                    "category": category,
                    "month": this_start.strftime("%Y-%m"),
                    "current": float(current_amount),
                    "previous": float(previous_amount),
                    "pct_change": round(pct_change, 1),
                }
            )

    changes.sort(key=lambda c: abs(c["pct_change"]), reverse=True)
    return changes