from equipment.serializers import EquipmentReadingSerializer, EquipmentSerializer
from hospital.serializers import (
    AdmissionSerializer,
    BedSerializer,
    EmergencyArrivalSerializer,
    VitalReadingSerializer,
)

from .broadcast import broadcast


def bed_changed(bed):
    broadcast("bed_update", BedSerializer(bed).data)


def admission_changed(admission, action):
    broadcast("admission_update", {"action": action, **AdmissionSerializer(admission).data})


def vitals_recorded(reading):
    broadcast("vitals", {"admission": reading.admission_id, **VitalReadingSerializer(reading).data})


def emergency_changed(arrival):
    broadcast("emergency_update", EmergencyArrivalSerializer(arrival).data)


def equipment_changed(equipment):
    broadcast("equipment_update", EquipmentSerializer(equipment).data)


def telemetry_recorded(reading):
    broadcast("telemetry", {"equipment": reading.equipment_id, **EquipmentReadingSerializer(reading).data})


def clock_ticked(clock):
    broadcast("clock", {"hospital_time": clock.now(), "running": clock.running, "speed": clock.speed})
