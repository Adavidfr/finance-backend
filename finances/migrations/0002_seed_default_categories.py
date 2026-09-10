from django.db import migrations

DEFAULT_CATEGORIES = [
    # (nombre, tipo, icono, color)
    ("Salario", "income", "💰", "#22C55E"),
    ("Freelance", "income", "💻", "#16A34A"),
    ("Otros ingresos", "income", "➕", "#15803D"),
    ("Comida", "expense", "🍔", "#F97316"),
    ("Transporte", "expense", "🚗", "#3B82F6"),
    ("Vivienda", "expense", "🏠", "#8B5CF6"),
    ("Servicios", "expense", "💡", "#EAB308"),
    ("Entretenimiento", "expense", "🎬", "#EC4899"),
    ("Salud", "expense", "🏥", "#EF4444"),
    ("Educación", "expense", "📚", "#06B6D4"),
    ("Compras", "expense", "🛍️", "#A855F7"),
    ("Otros gastos", "expense", "📦", "#6B7280"),
]


def create_default_categories(apps, schema_editor):
    Category = apps.get_model("finances", "Category")
    for name, category_type, icon, color in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(
            name=name,
            category_type=category_type,
            user=None,  # categorías del sistema, no de un usuario específico
            defaults={"icon": icon, "color": color, "is_default": True},
        )


def remove_default_categories(apps, schema_editor):
    Category = apps.get_model("finances", "Category")
    Category.objects.filter(is_default=True, user=None).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("finances", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_categories, remove_default_categories),
    ]