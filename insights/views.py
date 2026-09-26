from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Insight
from .serializers import InsightSerializer
from .services import generate_all_insights


class InsightViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InsightSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Insight.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Dispara el cálculo + redacción de los 3 tipos de insight para el usuario."""
        insights = generate_all_insights(request.user)
        serializer = InsightSerializer(insights, many=True)
        return Response(serializer.data)