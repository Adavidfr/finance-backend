import pandas as pd
from django.db import transaction as db_transaction

from finances.models import Transaction

# Nombres de columna que aceptamos, mapeados a los campos del modelo.
# Así soportamos CSVs con encabezados en español o inglés sin romper nada.
COLUMN_ALIASES = {
    "date": ["date", "fecha"],
    "description": ["description", "descripcion", "descripción", "detalle"],
    "amount": ["amount", "monto", "valor"],
}


def _find_column(df_columns, aliases):
    """Busca cuál de los nombres alternativos existe realmente en el CSV."""
    lower_columns = {col.lower().strip(): col for col in df_columns}
    for alias in aliases:
        if alias in lower_columns:
            return lower_columns[alias]
    return None


def parse_csv(file_path):
    """
    Lee el CSV y devuelve una lista de diccionarios listos para crear
    Transactions. Lanza ValueError con un mensaje claro si falta una
    columna requerida.
    """
    df = pd.read_csv(file_path)

    date_col = _find_column(df.columns, COLUMN_ALIASES["date"])
    description_col = _find_column(df.columns, COLUMN_ALIASES["description"])
    amount_col = _find_column(df.columns, COLUMN_ALIASES["amount"])

    missing = [
        name for name, col in [("date", date_col), ("description", description_col), ("amount", amount_col)]
        if col is None
    ]
    if missing:
        raise ValueError(
            f"El CSV no tiene las columnas requeridas: {', '.join(missing)}. "
            f"Columnas encontradas: {list(df.columns)}"
        )

    rows = []
    for _, row in df.iterrows():
        rows.append(
            {
                "date": pd.to_datetime(row[date_col]).date(),
                "description": str(row[description_col]).strip(),
                "raw_description": str(row[description_col]).strip(),
                "amount": row[amount_col],
            }
        )
    return rows


def create_transactions_from_rows(rows, account):
    """
    Crea las Transaction en bulk. Devuelve la lista de IDs creados
    (para poder categorizarlas después, una por una, vía Celery).
    """
    with db_transaction.atomic():
        transactions = [
            Transaction(
                account=account,
                date=row["date"],
                description=row["description"],
                raw_description=row["raw_description"],
                amount=row["amount"],
                source=Transaction.Source.IMPORT,
            )
            for row in rows
        ]
        created = Transaction.objects.bulk_create(transactions)
    return [t.id for t in created]