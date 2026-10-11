from rest_framework import serializers

from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    acknowledged_by = serializers.CharField(source="acknowledged_by.username", read_only=True, default=None)
    resolved_by = serializers.CharField(source="resolved_by.username", read_only=True, default=None)
    patient_id = serializers.IntegerField(source="admission.patient_id", read_only=True, default=None)
    bed = serializers.CharField(source="admission.bed.code", read_only=True, default=None)
    equipment_code = serializers.CharField(source="equipment.code", read_only=True, default=None)
    unit_code = serializers.CharField(source="unit.code", read_only=True, default=None)

    class Meta:
        model = Alert
        fields = (
            "id", "kind", "severity", "status", "message", "value",
            "admission", "patient_id", "bed", "equipment", "equipment_code", "unit", "unit_code",
            "created_at", "last_seen_at",
            "acknowledged_at", "acknowledged_by", "resolved_at", "resolved_by",
        )
        read_only_fields = fields


class ThresholdSerializer(serializers.Serializer):
    """One alert rule's limits, for the admin's thresholds screen (S27)."""

    key = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    kind = serializers.CharField(read_only=True)
    unit = serializers.CharField(read_only=True)
    direction = serializers.CharField(read_only=True)
    warning = serializers.FloatField()
    critical = serializers.FloatField()
    clear = serializers.FloatField()
    is_default = serializers.BooleanField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True, allow_null=True)
    updated_by = serializers.CharField(read_only=True, allow_null=True)
