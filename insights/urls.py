from rest_framework.routers import DefaultRouter

from .views import InsightViewSet

router = DefaultRouter()
router.register("insights", InsightViewSet, basename="insight")

urlpatterns = router.urls