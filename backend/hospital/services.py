from django.db import transaction
from twin import clock, events
from config.errors import DomainError
from twin import clock

from .models import Admission, Bed, EmergencyArrival, Transfer, VitalReading


class HospitalError(DomainError):
    """Raised when an action breaks a hospital rule, e.g. admitting into an occupied bed."""


def _lock_bed(bed_id):
    return Bed.objects.select_for_update().get(pk=bed_id)


def _set_bed_status(bed, status, at):
    bed.status = status
    bed.status_since = at
    bed.save(update_fields=["status", "status_since"])
    events.bed_changed(bed)


@transaction.atomic
def admit_patient(*, patient, bed, reason="", by=None, admitted_at=None,
                  expected_discharge_at=None, emergency_arrival=None):
    admitted_at = admitted_at or clock.now()
    bed = _lock_bed(bed.pk)
    if not bed.is_active:
        raise HospitalError(f"Bed {bed.code} is closed.")
    if bed.status != Bed.Status.FREE:
        raise HospitalError(f"Bed {bed.code} is not free.")
    if emergency_arrival is not None and emergency_arrival.status != EmergencyArrival.Status.WAITING:
        raise HospitalError("This emergency patient is no longer waiting.")
    if patient.admissions.filter(discharged_at__isnull=True).exists():
        raise HospitalError(f"{patient.full_name} is already admitted.")

    admission = Admission.objects.create(
        patient=patient,
        bed=bed,
        reason=reason,
        admitted_at=admitted_at,
        expected_discharge_at=expected_discharge_at,
        admitted_by=by,
    )
    _set_bed_status(bed, Bed.Status.OCCUPIED, admitted_at)

    if emergency_arrival is not None:
        emergency_arrival.status = EmergencyArrival.Status.ADMITTED
        emergency_arrival.admission = admission
        emergency_arrival.save(update_fields=["status", "admission"])
        events.emergency_changed(emergency_arrival)

    events.admission_changed(admission, "admitted")
    return admission


@transaction.atomic
def transfer_patient(*, admission, to_bed, by=None, transferred_at=None, expected_discharge_at=None):
    transferred_at = transferred_at or clock.now()
    if not admission.is_active:
        raise HospitalError("Only current admissions can be transferred.")
    if to_bed.pk == admission.bed_id:
        raise HospitalError("The patient is already in that bed.")

    beds = Bed.objects.select_for_update().in_bulk([admission.bed_id, to_bed.pk])
    from_bed, to_bed = beds[admission.bed_id], beds[to_bed.pk]
    if not to_bed.is_active or to_bed.status != Bed.Status.FREE:
        raise HospitalError(f"Bed {to_bed.code} is not available.")

    Transfer.objects.create(
        admission=admission,
        from_bed=from_bed,
        to_bed=to_bed,
        transferred_at=transferred_at,
        transferred_by=by,
    )
    admission.bed = to_bed
    fields = ["bed"]
    if expected_discharge_at is not None:
        admission.expected_discharge_at = expected_discharge_at
        fields.append("expected_discharge_at")
    admission.save(update_fields=fields)
    _set_bed_status(from_bed, Bed.Status.CLEANING, transferred_at)
    _set_bed_status(to_bed, Bed.Status.OCCUPIED, transferred_at)
    
    events.admission_changed(admission, "transferred")
    return admission


@transaction.atomic
def discharge_patient(*, admission, outcome, by=None, discharged_at=None):
    discharged_at = discharged_at or clock.now()
    if not admission.is_active:
        raise HospitalError("This admission has already ended.")

    bed = _lock_bed(admission.bed_id)
    admission.discharged_at = discharged_at
    admission.outcome = outcome
    admission.discharged_by = by
    admission.save(update_fields=["discharged_at", "outcome", "discharged_by"])
    _set_bed_status(bed, Bed.Status.CLEANING, discharged_at)
    events.admission_changed(admission, "discharged")

    return admission


@transaction.atomic
def mark_bed_clean(*, bed, at=None):
    bed = _lock_bed(bed.pk)
    if bed.status != Bed.Status.CLEANING:
        raise HospitalError(f"Bed {bed.code} is not waiting for cleaning.")
    _set_bed_status(bed, Bed.Status.FREE, at or clock.now())
    return bed


def record_vitals(*, admission, source=VitalReading.Source.MONITOR, by=None, recorded_at=None, **values):
    if not admission.is_active:
        raise HospitalError("Vitals can only be recorded for current admissions.")
    if not any(value is not None for value in values.values()):
        raise HospitalError("At least one vital sign is required.")

    reading = VitalReading(
        admission=admission,
        source=source,
        recorded_by=by,
        recorded_at=recorded_at or clock.now(),
        **values,
    )
    reading.full_clean()
    reading.save()
    events.vitals_recorded(reading)
    return reading


def discharge_from_emergency(*, arrival):
    if arrival.status != EmergencyArrival.Status.WAITING:
        raise HospitalError("This emergency patient is no longer waiting.")
    arrival.status = EmergencyArrival.Status.DISCHARGED
    arrival.save(update_fields=["status"])
    events.emergency_changed(arrival)
    return arrival


def log_emergency_arrival(*, patient, triage_level, complaint, by=None, arrived_at=None):
    arrival = EmergencyArrival.objects.create(
        patient=patient,
        triage_level=triage_level,
        complaint=complaint,
        logged_by=by,
        arrived_at=arrived_at or clock.now(),
    )
    events.emergency_changed(arrival)
    return arrival
