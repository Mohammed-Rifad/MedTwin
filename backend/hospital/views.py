from django.db.models import Count, Prefetch, Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.audit import log_action
from accounts.models import AuditLog, User
from accounts.permissions import IsAdminOrReadOnly, RolePermissionMixin

from . import services
from .filters import AdmissionFilter, PatientFilter
from .models import Admission, Bed, EmergencyArrival, Patient, Unit, VitalReading
from .serializers import (
    AdmissionSerializer,
    AdmitSerializer,
    BedSerializer,
    DischargeSerializer,
    EmergencyAdmitSerializer,
    EmergencyArrivalSerializer,
    PatientDetailSerializer,
    PatientSerializer,
    TransferSerializer,
    UnitSerializer,
    VitalReadingSerializer,
)

ADMIN, DOCTOR, NURSE = User.Role.ADMIN, User.Role.DOCTOR, User.Role.NURSE
NO_PUT_OR_DELETE = ["get", "post", "patch", "head", "options"]


def with_current_admission():
    return Prefetch(
        "admissions",
        queryset=Admission.objects.filter(discharged_at__isnull=True).select_related("patient", "bed"),
        to_attr="current_admissions",
    )


class UnitViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSerializer
    permission_classes = [IsAdminOrReadOnly]
    http_method_names = NO_PUT_OR_DELETE

    def get_queryset(self):
        active = Q(beds__is_active=True)
        return Unit.objects.annotate(
            _capacity=Count("beds", filter=active),
            _occupied=Count("beds", filter=active & Q(beds__status=Bed.Status.OCCUPIED)),
        ).order_by("floor", "name")



class BedViewSet(viewsets.ModelViewSet):
    serializer_class = BedSerializer
    permission_classes = [IsAdminOrReadOnly]
    http_method_names = NO_PUT_OR_DELETE
    filterset_fields = ["unit", "status", "is_active"]
    search_fields = ["code"]

    def get_queryset(self):
        return Bed.objects.select_related("unit").prefetch_related(with_current_admission())

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def clean(self, request, pk=None):
        bed = services.mark_bed_clean(bed=self.get_object())
        return Response(self.get_serializer(bed).data)


class PatientViewSet(RolePermissionMixin, viewsets.ModelViewSet):
    http_method_names = NO_PUT_OR_DELETE
    filterset_class = PatientFilter
    search_fields = ["mrn", "first_name", "last_name"]
    ordering_fields = ["last_name", "created_at"]
    action_roles = {"create": (NURSE, ADMIN), "partial_update": (NURSE, ADMIN)}

    def get_queryset(self):
        queryset = Patient.objects.prefetch_related(with_current_admission())
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("admissions__bed__unit")
        return queryset

    def get_serializer_class(self):
        return PatientDetailSerializer if self.action == "retrieve" else PatientSerializer

    def retrieve(self, request, *args, **kwargs):
        patient = self.get_object()
        log_action(request, AuditLog.Action.VIEW, patient, "Viewed patient record")
        return Response(self.get_serializer(patient).data)

    def perform_create(self, serializer):
        patient = serializer.save()
        log_action(self.request, AuditLog.Action.CREATE, patient, "Registered patient")

    def perform_update(self, serializer):
        patient = serializer.save()
        log_action(self.request, AuditLog.Action.UPDATE, patient, "Updated patient details")


class AdmissionViewSet(
    RolePermissionMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Admission.objects.select_related("patient", "bed__unit")
    serializer_class = AdmissionSerializer
    filterset_class = AdmissionFilter
    ordering_fields = ["admitted_at", "risk_score"]
    action_roles = {
        "create": (NURSE, ADMIN),
        "transfer": (DOCTOR, NURSE),
        "discharge": (DOCTOR,),
        "record_vitals": (NURSE,),
    }

    def create(self, request):
        data = AdmitSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        admission = services.admit_patient(by=request.user, **data.validated_data)
        log_action(request, AuditLog.Action.CREATE, admission, f"Admitted to {admission.bed.code}")
        return Response(AdmissionSerializer(admission).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def transfer(self, request, pk=None):
        data = TransferSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        admission = services.transfer_patient(
            admission=self.get_object(), to_bed=data.validated_data["to_bed"], by=request.user
        )
        log_action(request, AuditLog.Action.UPDATE, admission, f"Transferred to {admission.bed.code}")
        return Response(AdmissionSerializer(admission).data)

    @action(detail=True, methods=["post"])
    def discharge(self, request, pk=None):
        data = DischargeSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        admission = services.discharge_patient(
            admission=self.get_object(), outcome=data.validated_data["outcome"], by=request.user
        )
        log_action(request, AuditLog.Action.UPDATE, admission, f"Discharged ({admission.outcome})")
        return Response(AdmissionSerializer(admission).data)

    @action(detail=True, methods=["get"])
    def vitals(self, request, pk=None):
        page = self.paginate_queryset(self.get_object().vitals.all())
        return self.get_paginated_response(VitalReadingSerializer(page, many=True).data)

    @vitals.mapping.post
    def record_vitals(self, request, pk=None):
        data = VitalReadingSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        reading = services.record_vitals(
            admission=self.get_object(),
            source=VitalReading.Source.MANUAL,
            by=request.user,
            **data.validated_data,
        )
        return Response(VitalReadingSerializer(reading).data, status=status.HTTP_201_CREATED)


class EmergencyArrivalViewSet(
    RolePermissionMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = EmergencyArrival.objects.select_related("patient")
    serializer_class = EmergencyArrivalSerializer
    filterset_fields = ["status", "triage_level"]
    action_roles = {
        "create": (NURSE, ADMIN),
        "admit": (NURSE, ADMIN),
        "discharge": (DOCTOR, NURSE),
    }

    def perform_create(self, serializer):
        arrival = serializer.save(logged_by=self.request.user)
        log_action(self.request, AuditLog.Action.CREATE, arrival, f"ED arrival, triage {arrival.triage_level}")

    @action(detail=True, methods=["post"])
    def admit(self, request, pk=None):
        arrival = self.get_object()
        data = EmergencyAdmitSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        admission = services.admit_patient(
            patient=arrival.patient,
            bed=data.validated_data["bed"],
            reason=data.validated_data.get("reason") or arrival.complaint,
            by=request.user,
            emergency_arrival=arrival,
        )
        log_action(request, AuditLog.Action.CREATE, admission, f"Admitted from ED to {admission.bed.code}")
        return Response(AdmissionSerializer(admission).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def discharge(self, request, pk=None):
        arrival = services.discharge_from_emergency(arrival=self.get_object())
        log_action(request, AuditLog.Action.UPDATE, arrival, "Discharged from ED")
        return Response(self.get_serializer(arrival).data)
