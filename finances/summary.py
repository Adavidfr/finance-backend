from datetime import date

from dateutil.relativedelta import relativedelta
from django.db.models import Sum

from .models import Category, Transaction


def get_spending_by_category(user, start=None, end=None):
    """
    Gasto total agrupado por categoría, en el rango de fechas dado.
    Si no se especifica rango, usa el mes actual.
    Pensado para alimentar un gráfico de pastel/barras en el frontend.
    """
    if start is None or end is None:
        today = date.today()
        start = today.replace(day=1)
        end = today

    qs = (
        Transaction.objects.filter(
            account__user=user, date__gte=start, date__lte=end, amount__lt=0, category__isnull=False
        )
        .values("category__id", "category__name", "category__color", "category__icon")
        .annotate(total=Sum("amount"))
        .order_by("-total")
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


def get_monthly_trend(user, months=6):
    """
    Evolución de ingresos y gastos totales, mes a mes, para los últimos
    N meses. Pensado para un gráfico de líneas/barras de evolución mensual.
    """
    today = date.today()
    trend = []

    for i in range(months - 1, -1, -1):
        month_start = (today.replace(day=1)) - relativedelta(months=i)
        month_end = (month_start + relativedelta(months=1)) - relativedelta(days=1)

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


def get_dashboard_summary(user):
    """Un solo payload con todo lo que necesita la pantalla principal del dashboard."""
    today = date.today()
    month_start = today.replace(day=1)

    total_income = Transaction.objects.filter(
        account__user=user, date__gte=month_start, date__lte=today, amount__gt=0
    ).aggregate(total=Sum("amount"))["total"] or 0

    total_expenses = Transaction.objects.filter(
        account__user=user, date__gte=month_start, date__lte=today, amount__lt=0
    ).aggregate(total=Sum("amount"))["total"] or 0

    return {
        "current_month": {
            "income": float(total_income),
            "expenses": abs(float(total_expenses)),
            "balance": float(total_income) - abs(float(total_expenses)),
        },
        "spending_by_category": get_spending_by_category(user),
        "monthly_trend": get_monthly_trend(user),
    }