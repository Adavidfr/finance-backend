from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AccountViewSet, CategoryViewSet, DashboardSummaryView, TransactionViewSet

router = DefaultRouter()
router.register("accounts", AccountViewSet, basename="account")
router.register("categories", CategoryViewSet, basename="category")
router.register("transactions", TransactionViewSet, basename="transaction")

urlpatterns = router.urls + [
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
]