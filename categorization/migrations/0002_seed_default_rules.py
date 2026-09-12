from django.db import migrations

DEFAULT_RULES = [
    ("UBER", "Transporte"),
    ("CABIFY", "Transporte"),
    ("TAXI", "Transporte"),
    ("GASOLINA", "Transporte"),
    ("NETFLIX", "Entretenimiento"),
    ("SPOTIFY", "Entretenimiento"),
    ("DISNEY", "Entretenimiento"),
    ("CINE", "Entretenimiento"),
    ("SUPERMAXI", "Comida"),
    ("MEGAMAXI", "Comida"),
    ("RESTAURANTE", "Comida"),
    ("MCDONALD", "Comida"),
    ("KFC", "Comida"),
    ("FARMACIA", "Salud"),
    ("HOSPITAL", "Salud"),
    ("CLINICA", "Salud"),
    ("ARRIENDO", "Vivienda"),
    ("ALQUILER", "Vivienda"),
    ("LUZ", "Servicios"),
    ("AGUA", "Servicios"),
    ("INTERNET", "Servicios"),
    ("CLARO", "Servicios"),
    ("MOVISTAR", "Servicios"),
]


def create_default_rules(apps, schema_editor):
    CategoryRule = apps.get_model("categorization", "CategoryRule")
    Category = apps.get_model("finances", "Category")

    for keyword, category_name in DEFAULT_RULES:
        try:
            category = Category.objects.get(name=category_name, user=None)
        except Category.DoesNotExist:
            continue
        CategoryRule.objects.get_or_create(keyword=keyword, category=category, user=None)


def remove_default_rules(apps, schema_editor):
    CategoryRule = apps.get_model("categorization", "CategoryRule")
    CategoryRule.objects.filter(user=None).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("categorization", "0001_initial"),
        ("finances", "0002_seed_default_categories"),
    ]

    operations = [
        migrations.RunPython(create_default_rules, remove_default_rules),
    ]