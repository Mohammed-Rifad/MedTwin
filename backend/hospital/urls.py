from rest_framework.routers import DefaultRouter

from . import views

app_name = "hospital"

router = DefaultRouter()
router.register("units", views.UnitViewSet, basename="units")
router.register("beds", views.BedViewSet, basename="beds")
router.register("patients", views.PatientViewSet, basename="patients")
router.register("admissions", views.AdmissionViewSet, basename="admissions")
router.register("emergency", views.EmergencyArrivalViewSet, basename="emergency")

urlpatterns = router.urls
