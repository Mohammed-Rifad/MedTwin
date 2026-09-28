from django.db import transaction
from django.utils import timezone

from .models import Admission, Bed, EmergencyArrival, Transfer, VitalReading


class HospitalError(Exception):
    """Raised when an action breaks a hospital rule, e.g. admitting into an occupied bed."""


def _lock_bed(bed_id):
    return Bed.objects.select_for_update().get(pk=bed_id)


@transaction.atomic
def admit_patient(*, patient, bed, reason="", by=None, admitted_at=None,
                  expected_discharge_at=None, emergency_arrival=None):
    bed = _lock_bed(bed.pk)
    if not bed.is_active:
        raise HospitalError(f"Bed {bed.code} is closed.")
    if bed.status != Bed.Status.FREE:
        raise HospitalError(f"Bed {bed.code} is not free.")
    if patient.admissions.filter(discharged_at__isnull=True).exists():
        raise HospitalError(f"{patient.full_name} is already admitted.")

    admission = Admission.objects.create(
        patient=patient,
        bed=bed,
        reason=reason,
        admitted_at=admitted_at or timezone.now(),
        expected_discharge_at=expected_discharge_at,
        admitted_by=by,
    )
    bed.status = Bed.Status.OCCUPIED
    bed.save(update_fields=["status"])

    if emergency_arrival is not None:
        emergency_arrival.status = EmergencyArrival.Status.ADMITTED
        emergency_arrival.admission = admission
        emergency_arrival.save(update_fields=["status", "admission"])

    return admission


@transaction.atomic
def transfer_patient(*, admission, to_bed, by=None, transferred_at=None):
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
        transferred_at=transferred_at or timezone.now(),
        transferred_by=by,
    )
    admission.bed = to_bed
    admission.save(update_fields=["bed"])
    from_bed.status = Bed.Status.CLEANING
    from_bed.save(update_fields=["status"])
    to_bed.status = Bed.Status.OCCUPIED
    to_bed.save(update_fields=["status"])
    return admission


@transaction.atomic
def discharge_patient(*, admission, outcome, by=None, discharged_at=None):
    if not admission.is_active:
        raise HospitalError("This admission has already ended.")

    bed = _lock_bed(admission.bed_id)
    admission.discharged_at = discharged_at or timezone.now()
    admission.outcome = outcome
    admission.discharged_by = by
    admission.save(update_fields=["discharged_at", "outcome", "discharged_by"])
    bed.status = Bed.Status.CLEANING
    bed.save(update_fields=["status"])
    return admission


@transaction.atomic
def mark_bed_clean(*, bed):
    bed = _lock_bed(bed.pk)
    if bed.status != Bed.Status.CLEANING:
        raise HospitalError(f"Bed {bed.code} is not waiting for cleaning.")
    bed.status = Bed.Status.FREE
    bed.save(update_fields=["status"])
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
        recorded_at=recorded_at or timezone.now(),
        **values,
    )
    reading.full_clean()
    reading.save()
    return reading
