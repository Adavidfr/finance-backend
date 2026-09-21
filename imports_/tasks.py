from celery import shared_task
from django.utils import timezone

from categorization.tasks import categorize_transaction_task

from .models import ImportJob
from .services import create_transactions_from_rows, parse_file


@shared_task
def process_import_job(import_job_id):
    try:
        job = ImportJob.objects.get(id=import_job_id)
    except ImportJob.DoesNotExist:
        return f"ImportJob {import_job_id} no existe"

    job.status = ImportJob.Status.PROCESSING
    job.save(update_fields=["status"])

    try:
        rows = parse_file(job.file.path)
        job.total_rows = len(rows)
        job.save(update_fields=["total_rows"])

        transaction_ids = create_transactions_from_rows(rows, job.account)

        # Dispara la categorización de cada transacción creada
        for tx_id in transaction_ids:
            categorize_transaction_task.delay(tx_id)

        job.processed_rows = len(transaction_ids)
        job.status = ImportJob.Status.DONE
        job.completed_at = timezone.now()
        job.save(update_fields=["processed_rows", "status", "completed_at"])
        return f"ImportJob {import_job_id} completado: {len(transaction_ids)} transacciones creadas"

    except Exception as exc:
        job.status = ImportJob.Status.FAILED
        job.error_message = str(exc)
        job.save(update_fields=["status", "error_message"])
        return f"ImportJob {import_job_id} falló: {exc}"