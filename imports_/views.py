from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import ImportJob
from .serializers import ImportJobSerializer
from .tasks import process_import_job


class ImportJobViewSet(viewsets.ModelViewSet):
    serializer_class = ImportJobSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head"]  # solo lectura + creación, no editar/borrar

    def get_queryset(self):
        return ImportJob.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        job = serializer.save(user=self.request.user)
        process_import_job.delay(job.id)