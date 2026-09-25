from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Account, Category, Transaction
from .serializers import AccountSerializer, CategorySerializer, TransactionSerializer
from .summary import get_dashboard_summary


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from django.db.models import Q
        return Category.objects.filter(
            Q(user=self.request.user) | Q(user__isnull=True)
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(account__user=self.request.user)

    def perform_update(self, serializer):
        # Distinguimos el origen del PATCH por los campos que llegaron:
        # - solo "category" -> el usuario corrigió la categoría a mano (aprende regla)
        # - description/amount/date -> editó los datos del movimiento, la
        #   categoría anterior puede ya no aplicar, así que se re-categoriza
        #   desde cero (reglas -> LLM), igual que una transacción nueva.
        changed_fields = set(self.request.data.keys())

        if changed_fields == {"category"}:
            instance = serializer.save(
                categorization_method=Transaction.CategorizationMethod.MANUAL,
                categorization_confidence=1.0,
            )
            from categorization.services import learn_rule_from_correction
            learn_rule_from_correction(instance)
        else:
            instance = serializer.save(
                category=None,
                categorization_method=Transaction.CategorizationMethod.PENDING,
                categorization_confidence=None,
            )
            from categorization.tasks import categorize_transaction_task
            categorize_transaction_task.delay(instance.id)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """
        El usuario confirma que la categoría actual es correcta,
        sin cambiarla. Esto dispara el aprendizaje de una regla,
        igual que una corrección manual — así hasta los aciertos
        del LLM terminan "graduándose" a reglas con el tiempo.
        """
        transaction = self.get_object()

        if not transaction.category:
            return Response(
                {"detail": "Esta transacción no tiene categoría asignada todavía, no hay nada que confirmar."},
                status=400,
            )

        transaction.categorization_method = Transaction.CategorizationMethod.MANUAL
        transaction.categorization_confidence = 1.0
        transaction.save(update_fields=["categorization_method", "categorization_confidence"])

        from categorization.services import learn_rule_from_correction
        learn_rule_from_correction(transaction)

        return Response(TransactionSerializer(transaction).data)


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(get_dashboard_summary(request.user))