from twin import clock
from rest_framework import serializers
from .models import Admission, Bed, EmergencyArrival, Patient, Unit, VitalReading


def current_admission_of(obj):
    admissions = getattr(obj, "current_admissions", None)
    if admissions is None:
        admissions = list(
            obj.admissions.filter(discharged_at__isnull=True).select_related("patient", "bed")
        )
    return admissions[0] if admissions else None


class CurrentAdmissionSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(source="patient.id")
    patient_name = serializers.CharField(source="patient.full_name")
    bed = serializers.CharField(source="bed.code")

    class Meta:
        model = Admission
        fields = ("id", "patient_id", "patient_name", "bed", "admitted_at", "risk_score", "risk_level")


class UnitSerializer(serializers.ModelSerializer):
    capacity = serializers.SerializerMethodField()
    occupied = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = (
            "id", "name", "code", "unit_type", "floor",
            "map_x", "map_y", "map_width", "map_height", "capacity", "occupied",
        )

    def get_capacity(self, obj):
        return obj._capacity if hasattr(obj, "_capacity") else obj.capacity

    def get_occupied(self, obj):
        return obj._occupied if hasattr(obj, "_occupied") else obj.occupied_count


class BedSerializer(serializers.ModelSerializer):
    unit_code = serializers.CharField(source="unit.code", read_only=True)
    current_admission = serializers.SerializerMethodField()

    class Meta:
        model = Bed
        fields = ("id", "unit", "unit_code", "code", "status", "is_active", "map_x", "map_y", "current_admission")
        read_only_fields = ("status",)

    def get_current_admission(self, obj):
        admission = current_admission_of(obj)
        return CurrentAdmissionSerializer(admission).data if admission else None


class PatientSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(read_only=True)
    current_admission = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = (
            "id", "mrn", "first_name", "last_name", "date_of_birth", "sex",
            "age", "current_admission", "created_at",
        )
        read_only_fields = ("created_at",)

    def get_current_admission(self, obj):
        admission = current_admission_of(obj)
        return CurrentAdmissionSerializer(admission).data if admission else None


class AdmissionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    bed_code = serializers.CharField(source="bed.code", read_only=True)
    unit = serializers.CharField(source="bed.unit.code", read_only=True)
    length_of_stay_hours = serializers.SerializerMethodField()

    class Meta:
        model = Admission
        fields = (
            "id", "patient", "patient_name", "bed", "bed_code", "unit", "reason",
            "admitted_at", "expected_discharge_at", "discharged_at", "outcome",
            "risk_score", "risk_level", "length_of_stay_hours",
        )
        read_only_fields = fields

    def get_length_of_stay_hours(self, obj):
        return round(obj.length_of_stay.total_seconds() / 3600, 1)


class PatientDetailSerializer(PatientSerializer):
    admissions = AdmissionSerializer(many=True, read_only=True)

    class Meta(PatientSerializer.Meta):
        fields = PatientSerializer.Meta.fields + ("admissions",)


class AdmitSerializer(serializers.Serializer):
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())
    bed = serializers.PrimaryKeyRelatedField(queryset=Bed.objects.all())
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    expected_discharge_at = serializers.DateTimeField(required=False, allow_null=True)


class TransferSerializer(serializers.Serializer):
    to_bed = serializers.PrimaryKeyRelatedField(queryset=Bed.objects.all())


class DischargeSerializer(serializers.Serializer):
    outcome = serializers.ChoiceField(choices=Admission.Outcome.choices)


class VitalReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = VitalReading
        fields = (
            "id", "recorded_at", "heart_rate", "spo2", "systolic_bp", "diastolic_bp",
            "respiratory_rate", "temperature", "source", "recorded_by",
        )
        read_only_fields = ("source", "recorded_by")


class EmergencyArrivalSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    waiting_minutes = serializers.SerializerMethodField()

    class Meta:
        model = EmergencyArrival
        fields = (
            "id", "patient", "patient_name", "arrived_at", "triage_level",
            "complaint", "status", "admission", "waiting_minutes",
        )
        read_only_fields = ("arrived_at", "status", "admission")

    def get_waiting_minutes(self, obj):
            if obj.status != EmergencyArrival.Status.WAITING:
                return None
            return int((clock.now() - obj.arrived_at).total_seconds() // 60)


class EmergencyAdmitSerializer(serializers.Serializer):
    bed = serializers.PrimaryKeyRelatedField(queryset=Bed.objects.all())
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
