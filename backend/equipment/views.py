from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.audit import log_action
from accounts.models import AuditLog
from accounts.permissions import IsAdminOrReadOnly

from . import services
from .models import Equipment
from .serializers import (
    EquipmentDetailSerializer,
    EquipmentReadingSerializer,
    EquipmentSerializer,
    FinishMaintenanceSerializer,
    MaintenanceLogSerializer,
    StartMaintenanceSerializer,
)


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.select_related("unit", "bed")
    permission_classes = [IsAdminOrReadOnly]
    http_method_names = ["get", "post", "patch", "head", "options"]
    filterset_fields = ["kind", "status", "unit"]
    search_fields = ["code", "model_name"]

    def get_serializer_class(self):
        return EquipmentDetailSerializer if self.action == "retrieve" else EquipmentSerializer

    def perform_create(self, serializer):
        equipment = serializer.save()
        log_action(self.request, AuditLog.Action.CREATE, equipment, "Registered device")

    def perform_update(self, serializer):
        equipment = serializer.save()
        log_action(self.request, AuditLog.Action.UPDATE, equipment, "Updated device")

    @action(detail=True, methods=["post"], url_path="start-maintenance")
    def start_maintenance(self, request, pk=None):
        data = StartMaintenanceSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        equipment = services.start_maintenance(
            equipment=self.get_object(), reason=data.validated_data["reason"], by=request.user
        )
        log_action(request, AuditLog.Action.UPDATE, equipment, "Started maintenance")
        return Response(EquipmentDetailSerializer(equipment).data)

    @action(detail=True, methods=["post"], url_path="finish-maintenance")
    def finish_maintenance(self, request, pk=None):
        data = FinishMaintenanceSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        equipment = services.finish_maintenance(
            equipment=self.get_object(), notes=data.validated_data.get("notes", ""), by=request.user
        )
        log_action(request, AuditLog.Action.UPDATE, equipment, "Finished maintenance")
        return Response(EquipmentDetailSerializer(equipment).data)

    @action(detail=True, methods=["get"])
    def readings(self, request, pk=None):
        page = self.paginate_queryset(self.get_object().readings.all())
        return self.get_paginated_response(EquipmentReadingSerializer(page, many=True).data)

    @action(detail=True, methods=["get"], url_path="maintenance-logs")
    def maintenance_logs(self, request, pk=None):
        page = self.paginate_queryset(self.get_object().maintenance_logs.all())
        return self.get_paginated_response(MaintenanceLogSerializer(page, many=True).data)
