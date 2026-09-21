import pandas as pd
from django.db import transaction as db_transaction

from finances.models import Transaction

COLUMN_ALIASES = {
    "date": ["date", "fecha"],
    "description": ["description", "descripcion", "descripción", "detalle"],
    "amount": ["amount", "monto", "valor"],
}


def _find_column(df_columns, aliases):
    lower_columns = {col.lower().strip(): col for col in df_columns}
    for alias in aliases:
        if alias in lower_columns:
            return lower_columns[alias]
    return None


def parse_file(file_path):
    """
    Lee un CSV o un Excel (.xlsx/.xls) y devuelve una lista de diccionarios
    listos para crear Transactions. Lanza ValueError con un mensaje claro
    si falta una columna requerida o el formato no es soportado.
    """
    if str(file_path).lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_path)
    elif str(file_path).lower().endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        raise ValueError("Formato de archivo no soportado. Usa .csv o .xlsx")

    date_col = _find_column(df.columns, COLUMN_ALIASES["date"])
    description_col = _find_column(df.columns, COLUMN_ALIASES["description"])
    amount_col = _find_column(df.columns, COLUMN_ALIASES["amount"])

    missing = [
        name for name, col in [("date", date_col), ("description", description_col), ("amount", amount_col)]
        if col is None
    ]
    if missing:
        raise ValueError(
            f"El archivo no tiene las columnas requeridas: {', '.join(missing)}. "
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