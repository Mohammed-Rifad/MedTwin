from rest_framework.routers import DefaultRouter

from . import views

app_name = "equipment"

router = DefaultRouter()
router.register("", views.EquipmentViewSet, basename="equipment")

urlpatterns = router.urls
