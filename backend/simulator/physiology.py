import math
from datetime import timedelta

import numpy as np

from hospital import services
from hospital.models import Admission, Unit

from .models import PatientPhysiology

VITALS = ("heart_rate", "spo2", "systolic_bp", "diastolic_bp", "respiratory_rate", "temperature")

# (average, spread) for a stable adult patient
NORMAL = {
    "heart_rate": (78, 10), "spo2": (97, 1.2), "systolic_bp": (124, 14),
    "diastolic_bp": (76, 9), "respiratory_rate": (16, 2), "temperature": (36.8, 0.3),
}
# How far each value moves at the peak of a deterioration (a sepsis-like picture)
DETERIORATION = {
    "heart_rate": 35, "spo2": -9, "systolic_bp": -30,
    "diastolic_bp": -18, "respiratory_rate": 12, "temperature": 1.6,
}
# Random variation per hour
NOISE = {
    "heart_rate": 4, "spo2": 0.8, "systolic_bp": 5,
    "diastolic_bp": 4, "respiratory_rate": 1.5, "temperature": 0.15,
}
LIMITS = {
    "heart_rate": (20, 250), "spo2": (50, 100), "systolic_bp": (40, 250),
    "diastolic_bp": (20, 150), "respiratory_rate": (4, 60), "temperature": (30, 45),
}
# How ill each triage level is on arrival, as a fraction of a full deterioration
TRIAGE_ILLNESS = {1: 0.5, 2: 0.3, 3: 0.1, 4: 0.0, 5: 0.0}
REVERSION_PER_HOUR = 0.5


class VitalsSimulator:
    def __init__(self, simulator):
        self.sim = simulator
        self.current = {}  # admission id -> latest (unrounded) values

    @property
    def config(self):
        return self.sim.config

    def step(self, now):
        admissions = Admission.objects.filter(discharged_at__isnull=True).select_related(
            "bed__unit", "physiology", "emergency_arrival"
        )
        for admission in admissions:
            physiology = self.physiology_for(admission)
            self.escalate_if_needed(admission, physiology, now)
            self.record_due_readings(admission, physiology, now)

    def physiology_for(self, admission):
        try:
            return admission.physiology
        except PatientPhysiology.DoesNotExist:
            pass
        rng = np.random.default_rng([self.sim.seed, admission.pk, 3])
        arrival = getattr(admission, "emergency_arrival", None)
        illness = TRIAGE_ILLNESS[arrival.triage_level] if arrival else 0.0
        baseline = {
            name: float(rng.normal(mean, spread)) + illness * DETERIORATION[name]
            for name, (mean, spread) in NORMAL.items()
        }
        onset = None
        if rng.random() < self.config.deterioration_probability:
            hours = float(rng.uniform(*self.config.deterioration_onset_hours))
            onset = admission.admitted_at + timedelta(hours=hours)
        physiology = PatientPhysiology.objects.create(
            admission=admission, baseline=baseline, deterioration_onset_at=onset
        )
        admission.physiology = physiology
        return physiology

    def severity(self, physiology, now):
        """0 = patient's normal, 1 = peak of the deterioration."""
        onset = physiology.deterioration_onset_at
        if onset is None or now < onset:
            return 0.0
        to_peak = timedelta(hours=self.config.deterioration_hours_to_peak)
        if physiology.escalated_at is None:
            return min(1.0, (now - onset) / to_peak)
        at_escalation = min(1.0, (physiology.escalated_at - onset) / to_peak)
        recovered = (now - physiology.escalated_at) / timedelta(hours=self.config.recovery_hours)
        return max(0.0, at_escalation * (1 - recovered))

    def is_unwell(self, admission, now):
        physiology = getattr(admission, "physiology", None)
        return physiology is not None and self.severity(physiology, now) > 0.2

    def start_deterioration(self, admission, now):
        """Make a patient start deteriorating now (used by the simulator controls)."""
        physiology = self.physiology_for(admission)
        physiology.deterioration_onset_at = now
        physiology.escalated_at = None
        physiology.save(update_fields=["deterioration_onset_at", "escalated_at"])

    def escalate_if_needed(self, admission, physiology, now):
        if physiology.escalated_at is not None or self.severity(physiology, now) < 1.0:
            return
        if admission.bed.unit.unit_type != Unit.UnitType.ICU:
            bed = self.sim.free_bed(Unit.UnitType.ICU)
            if bed is None:
                return  # no ICU bed: the patient stays critically ill where they are
            services.transfer_patient(
                admission=admission, to_bed=bed, transferred_at=now,
                expected_discharge_at=now + self.sim.stay(self.config.icu_stay),
            )
        physiology.escalated_at = now
        physiology.save(update_fields=["escalated_at"])

    def record_due_readings(self, admission, physiology, now):
        interval = timedelta(minutes=self.config.reading_interval_minutes[admission.bed.unit.unit_type])
        if physiology.last_reading_at is None:
            due = max(admission.admitted_at, now - interval)
        else:
            due = physiology.last_reading_at + interval
        if due > now:
            return
        temperature_gap = timedelta(hours=self.config.temperature_interval_hours)
        while due <= now:
            values = self.next_values(admission, physiology, due, interval / timedelta(hours=1))
            if physiology.last_temperature_at and due - physiology.last_temperature_at < temperature_gap:
                values["temperature"] = None
            else:
                physiology.last_temperature_at = due
            services.record_vitals(admission=admission, recorded_at=due, **values)
            physiology.last_reading_at = due
            due += interval
        physiology.save(update_fields=["last_reading_at", "last_temperature_at"])

    def target(self, physiology, at):
        severity = self.severity(physiology, at)
        return {name: physiology.baseline[name] + severity * DETERIORATION[name] for name in VITALS}

    def next_values(self, admission, physiology, at, hours):
        target = self.target(physiology, at)
        current = self.current.get(admission.pk, target)
        pull = min(1.0, REVERSION_PER_HOUR * hours)
        values = {}
        for name in VITALS:
            value = (
                current[name]
                + pull * (target[name] - current[name])
                + NOISE[name] * math.sqrt(hours) * self.sim.rng.normal()
            )
            low, high = LIMITS[name]
            values[name] = min(max(value, low), high)
        self.current[admission.pk] = values
        return {name: round(value, 1) if name == "temperature" else round(value) for name, value in values.items()}
