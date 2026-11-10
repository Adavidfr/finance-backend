from datetime import date

from dateutil.relativedelta import relativedelta
from django.db.models import Sum

from .models import Transaction


def get_month_bounds(year, month):
    """Primer y último día del mes indicado."""
    start = date(year, month, 1)
    end = start + relativedelta(months=1) - relativedelta(days=1)
    return start, end


def get_spending_by_category(user, start, end):
    """
    Gasto total agrupado por categoría en el rango dado.
    Pensado para alimentar un gráfico de pastel/barras en el frontend.
    """
    qs = (
        Transaction.objects.filter(
            account__user=user,
            date__gte=start,
            date__lte=end,
            amount__lt=0,
            category__isnull=False,
        )
        .values("category__id", "category__name", "category__color", "category__icon")
        .annotate(total=Sum("amount"))
        .order_by("total")  # los totales son negativos: el más negativo = mayor gasto
    )

    return [
        {
            "category_id": row["category__id"],
            "category_name": row["category__name"],
            "color": row["category__color"],
            "icon": row["category__icon"],
            "amount": abs(float(row["total"])),
        }
        for row in qs
    ]


def get_monthly_trend(user, year, month, months=6):
    """
    Ingresos y gastos de los últimos N meses, terminando en el mes
    seleccionado. Pensado para el gráfico de evolución mensual.
    """
    selected = date(year, month, 1)
    trend = []

    for i in range(months - 1, -1, -1):
        month_start = selected - relativedelta(months=i)
        month_end = month_start + relativedelta(months=1) - relativedelta(days=1)

        income = Transaction.objects.filter(
            account__user=user, date__gte=month_start, date__lte=month_end, amount__gt=0
        ).aggregate(total=Sum("amount"))["total"] or 0

        expenses = Transaction.objects.filter(
            account__user=user, date__gte=month_start, date__lte=month_end, amount__lt=0
        ).aggregate(total=Sum("amount"))["total"] or 0

        trend.append(
            {
                "month": month_start.strftime("%Y-%m"),
                "income": float(income),
                "expenses": abs(float(expenses)),
            }
        )

    return trend


def get_transaction_stats(user, start, end):
    """
    Estadísticas rápidas del período: cuántas transacciones, la más
    grande y el promedio. Para un panel lateral, no para una gráfica.
    """
    qs = Transaction.objects.filter(account__user=user, date__gte=start, date__lte=end)

    amounts = [abs(float(t.amount)) for t in qs]
    if not amounts:
        return {
            "total_transactions": 0,
            "largest_transaction": 0.0,
            "average_transaction": 0.0,
        }

    return {
        "total_transactions": len(amounts),
        "largest_transaction": max(amounts),
        "average_transaction": round(sum(amounts) / len(amounts), 2),
    }


def get_dashboard_summary(user, year=None, month=None):
    """Un solo payload con todo lo que necesita el Dashboard para el mes elegido."""
    today = date.today()
    year = year or today.year
    month = month or today.month
    start, end = get_month_bounds(year, month)

    total_income = Transaction.objects.filter(
        account__user=user, date__gte=start, date__lte=end, amount__gt=0
    ).aggregate(total=Sum("amount"))["total"] or 0

    total_expenses = Transaction.objects.filter(
        account__user=user, date__gte=start, date__lte=end, amount__lt=0
    ).aggregate(total=Sum("amount"))["total"] or 0

    return {
        "current_month": {
            "income": float(total_income),
            "expenses": abs(float(total_expenses)),
            "balance": float(total_income) - abs(float(total_expenses)),
        },
        "spending_by_category": get_spending_by_category(user, start, end),
        "monthly_trend": get_monthly_trend(user, year, month),
        "stats": get_transaction_stats(user, start, end),
    }