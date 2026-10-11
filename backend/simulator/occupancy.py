"""Hourly occupancy per unit type, rebuilt from admissions and transfers (the input for the ICU forecast)."""

from datetime import timedelta

import numpy as np
from django.db.models import Prefetch

from hospital.models import Admission, Bed, EmergencyArrival, Transfer, Unit

UNIT_TYPES = [Unit.UnitType.ICU, Unit.UnitType.WARD, Unit.UnitType.ED]


def stay_segments(admission, now):
    """Yield (unit type, start, end) for each part of a stay: e.g. ED bay -> ICU bed -> ward bed."""
    transfers = list(admission.transfers.all())  # ordered by time
    bed = transfers[0].from_bed if transfers else admission.bed
    start = admission.admitted_at
    for transfer in transfers:
        yield bed.unit.unit_type, start, transfer.transferred_at
        bed, start = transfer.to_bed, transfer.transferred_at
    yield bed.unit.unit_type, start, admission.discharged_at or now


def hourly_occupancy(start, end):
    """
    Rows of {"time", "ICU", "WARD", "ED", "icu_admissions", "ed_arrivals"}: patients in each unit type on the hour,
    plus how many patients entered the ICU and arrived at the ED during the hour before.
    """
    hours = int((end - start) / timedelta(hours=1)) + 1
    changes = {unit_type: np.zeros(hours + 1, dtype=int) for unit_type in UNIT_TYPES}
    icu_admissions = np.zeros(hours, dtype=int)

    def hour_index(moment):
        return (moment - start) / timedelta(hours=1)

    admissions = Admission.objects.filter(admitted_at__lte=end).exclude(discharged_at__lt=start).select_related(
        "bed__unit"
    ).prefetch_related(Prefetch("transfers", queryset=Transfer.objects.select_related("from_bed__unit", "to_bed__unit")))

    for admission in admissions.iterator(chunk_size=500):
        for unit_type, segment_start, segment_end in stay_segments(admission, end):
            # Counted at hour h if the patient was in the unit at that exact moment: start <= h < end.
            first = max(0, int(np.ceil(hour_index(segment_start))))
            last = min(hours, int(np.ceil(hour_index(segment_end))))
            if first < last:
                changes[unit_type][first] += 1
                changes[unit_type][last] -= 1
            if unit_type == Unit.UnitType.ICU and 0 <= hour_index(segment_start) < hours:
                icu_admissions[min(hours - 1, int(np.ceil(hour_index(segment_start))))] += 1

    ed_arrivals = np.zeros(hours, dtype=int)
    for arrived_at in EmergencyArrival.objects.filter(arrived_at__range=(start, end)).values_list("arrived_at", flat=True):
        ed_arrivals[min(hours - 1, int(np.ceil(hour_index(arrived_at))))] += 1

    occupancy = {unit_type: np.cumsum(changes[unit_type])[:hours] for unit_type in UNIT_TYPES}
    for index in range(hours):
        yield {
            "time": start + timedelta(hours=index),
            "ICU": int(occupancy[Unit.UnitType.ICU][index]),
            "WARD": int(occupancy[Unit.UnitType.WARD][index]),
            "ED": int(occupancy[Unit.UnitType.ED][index]),
            "icu_admissions": int(icu_admissions[index]),
            "ed_arrivals": int(ed_arrivals[index]),
        }


def capacities():
    return {unit_type: Bed.objects.filter(unit__unit_type=unit_type, is_active=True).count() for unit_type in UNIT_TYPES}
