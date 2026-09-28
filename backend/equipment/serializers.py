from rest_framework import serializers

from .models import Equipment, EquipmentReading, MaintenanceLog


class EquipmentReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentReading
        fields = ("id", "recorded_at", "temperature", "running_hours", "error_count", "pressure")


class MaintenanceLogSerializer(serializers.ModelSerializer):
    started_by = serializers.CharField(source="started_by.username", read_only=True, default=None)
    finished_by = serializers.CharField(source="finished_by.username", read_only=True, default=None)

    class Meta:
        model = MaintenanceLog
        fields = ("id", "reason", "notes", "started_at", "finished_at", "started_by", "finished_by")


class EquipmentSerializer(serializers.ModelSerializer):
    unit_code = serializers.CharField(source="unit.code", read_only=True, default=None)
    bed_code = serializers.CharField(source="bed.code", read_only=True, default=None)

    class Meta:
        model = Equipment
        fields = (
            "id", "code", "kind", "model_name", "unit", "unit_code", "bed", "bed_code",
            "status", "installed_on", "last_serviced_at", "anomaly_score",
        )
        read_only_fields = ("status", "last_serviced_at", "anomaly_score")

    def validate(self, attrs):
        unit = attrs.get("unit", getattr(self.instance, "unit", None))
        bed = attrs.get("bed", getattr(self.instance, "bed", None))
        if bed is not None and unit is not None and bed.unit_id != unit.pk:
            raise serializers.ValidationError({"bed": f"Bed {bed.code} is not in {unit.name}."})
        return attrs


class EquipmentDetailSerializer(EquipmentSerializer):
    latest_reading = serializers.SerializerMethodField()
    open_maintenance = serializers.SerializerMethodField()

    class Meta(EquipmentSerializer.Meta):
        fields = EquipmentSerializer.Meta.fields + ("latest_reading", "open_maintenance")

    def get_latest_reading(self, obj):
        reading = obj.readings.first()
        return EquipmentReadingSerializer(reading).data if reading else None

    def get_open_maintenance(self, obj):
        log = obj.maintenance_logs.filter(finished_at__isnull=True).first()
        return MaintenanceLogSerializer(log).data if log else None


class StartMaintenanceSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255)


class FinishMaintenanceSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)
