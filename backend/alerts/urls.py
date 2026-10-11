from rest_framework.routers import DefaultRouter

from . import views

app_name = "alerts"

router = DefaultRouter()
# "thresholds" must be registered first: otherwise /api/alerts/thresholds/ would be read as an alert with id "thresholds".
router.register("thresholds", views.ThresholdViewSet, basename="thresholds")
router.register("", views.AlertViewSet, basename="alerts")

urlpatterns = router.urls
