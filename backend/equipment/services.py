from django.db import transaction
from twin import clock
from config.errors import DomainError
from .models import Equipment, EquipmentReading, MaintenanceLog
from twin import clock, events


class EquipmentError(DomainError):
    """Raised when an action breaks an equipment rule."""


def _lock(equipment):
    return Equipment.objects.select_for_update().get(pk=equipment.pk)


@transaction.atomic
def start_maintenance(*, equipment, reason, by=None, at=None):
    equipment = _lock(equipment)
    if equipment.status == Equipment.Status.MAINTENANCE:
        raise EquipmentError(f"{equipment.code} is already in maintenance.")
    
    MaintenanceLog.objects.create(
        equipment=equipment, reason=reason, started_by=by, started_at=at or clock.now()
    )

    equipment.status = Equipment.Status.MAINTENANCE
    equipment.save(update_fields=["status"])
    events.equipment_changed(equipment)

    return equipment


@transaction.atomic
def finish_maintenance(*, equipment, notes="", by=None, at=None):
    equipment = _lock(equipment)
    if equipment.status != Equipment.Status.MAINTENANCE:
        raise EquipmentError(f"{equipment.code} is not in maintenance.")
    
    now = at or clock.now()

    log = equipment.maintenance_logs.filter(finished_at__isnull=True).first()
    if log is not None:
        log.finished_at = now
        log.finished_by = by
        log.notes = notes
        log.save(update_fields=["finished_at", "finished_by", "notes"])
    equipment.status = Equipment.Status.OK
    equipment.last_serviced_at = now
    equipment.anomaly_score = None
    equipment.save(update_fields=["status", "last_serviced_at", "anomaly_score"])
    events.equipment_changed(equipment)

    return equipment


def record_telemetry(*, equipment, recorded_at=None, **values):
    if equipment.status == Equipment.Status.MAINTENANCE:
        raise EquipmentError(f"{equipment.code} is in maintenance and not sending data.")
    reading = EquipmentReading.objects.create(
        equipment=equipment, recorded_at=recorded_at or clock.now(), **values
    )
    events.telemetry_recorded(reading)
    return reading


@transaction.atomic
def mark_failed(*, equipment):
    equipment = _lock(equipment)
    if equipment.status in (Equipment.Status.MAINTENANCE, Equipment.Status.FAULT):
        raise EquipmentError(f"{equipment.code} cannot fail while {equipment.get_status_display().lower()}.")
    equipment.status = Equipment.Status.FAULT
    equipment.save(update_fields=["status"])
    events.equipment_changed(equipment)
    return equipment
