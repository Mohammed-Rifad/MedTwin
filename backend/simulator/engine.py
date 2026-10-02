import math
from datetime import timedelta
from .devices import DeviceSimulator
from .physiology import VitalsSimulator
import numpy as np
from django.utils import timezone
from faker import Faker

from hospital import services
from hospital.models import Admission, Bed, EmergencyArrival, Patient, Unit, VitalReading
from equipment import services as equipment_services
from equipment.models import EquipmentReading
from hospital.models import Admission, Bed, EmergencyArrival, Patient, Unit, VitalReading
from .config import COMPLAINTS, SimulationConfig

STAGE = {Unit.UnitType.ED: 0, Unit.UnitType.ICU: 1, Unit.UnitType.WARD: 2}


class Simulator:
    
    def __init__(self, config=None, seed=None, history=False):
        self.config = config or SimulationConfig()
        self.seed = seed if seed is not None else int(np.random.SeedSequence().entropy % 2**32)
        self.rng = np.random.default_rng(self.seed)
        self.fake = Faker(self.config.name_locale)
        self.fake.seed_instance(self.seed)
        self.history = history
        self.vital_buffer = []
        self.telemetry_buffer = []
        self.vitals = VitalsSimulator(self)
        self.devices = DeviceSimulator(self)


    def step(self, now, hours):
        """Advance the hospital by `hours` of hospital time, ending at `now`."""
        self.create_ed_arrivals(now, hours)
        self.create_elective_admissions(now, hours)
        self.move_ed_queue_into_bays(now)
        self.process_due_admissions(now)
        self.clean_beds(now)
        self.vitals.step(now)
        self.devices.step(now)

    # ---------- arrivals ----------

    def arrival_rate(self, now):
        local = timezone.localtime(now)
        c = self.config
        return c.ed_arrivals_per_hour * c.hourly_pattern[local.hour] * c.weekday_pattern[local.weekday()]

    def create_ed_arrivals(self, now, hours):
        for _ in range(self.rng.poisson(self.arrival_rate(now) * hours)):
            triage = int(self.rng.choice([1, 2, 3, 4, 5], p=self.config.triage_probabilities))
            EmergencyArrival.objects.create(
                patient=self.new_patient(now),
                triage_level=triage,
                complaint=str(self.rng.choice(COMPLAINTS[triage])),
                arrived_at=now - timedelta(hours=hours * self.rng.random()),
            )

    def create_elective_admissions(self, now, hours):
        if not 8 <= timezone.localtime(now).hour < 16:
            return
        for _ in range(self.rng.poisson(self.config.elective_admissions_per_day / 8 * hours)):
            bed = self.free_bed(Unit.UnitType.WARD)
            if bed is None:
                return  # no bed: planned admissions are postponed
            services.admit_patient(
                patient=self.new_patient(now),
                bed=bed,
                reason="Planned surgery",
                admitted_at=now,
                expected_discharge_at=now + self.stay(self.config.ward_stay),
            )

    def move_ed_queue_into_bays(self, now):
        waiting = EmergencyArrival.objects.filter(status=EmergencyArrival.Status.WAITING).select_related("patient")
        for arrival in waiting:  # already ordered by triage level, then arrival time
            bay = self.free_bed(Unit.UnitType.ED)
            if bay is None:
                return
            services.admit_patient(
                patient=arrival.patient,
                bed=bay,
                reason=arrival.complaint,
                admitted_at=now,
                expected_discharge_at=now + self.stay(self.config.ed_stay),
                emergency_arrival=arrival,
            )

    # ---------- end of each stay ----------

    def process_due_admissions(self, now):
        due = Admission.objects.filter(
            discharged_at__isnull=True, expected_discharge_at__lte=now
        ).select_related("bed__unit", "emergency_arrival","physiology")
        for admission in due:
            unit_type = admission.bed.unit.unit_type
            decide = self.decision_rng(admission, unit_type)
            if unit_type == Unit.UnitType.ED:
                self.finish_ed_stay(admission, now, decide)
            elif unit_type == Unit.UnitType.ICU:
                self.finish_icu_stay(admission, now, decide)
            else:
                self.finish_ward_stay(admission, now, decide)

    def finish_ed_stay(self, admission, now, decide):
        arrival = getattr(admission, "emergency_arrival", None)
        p_icu, p_ward = self.config.ed_disposition[arrival.triage_level if arrival else 3]
        roll = decide.random()
        if roll < p_icu:
            self.move_or_board(admission, Unit.UnitType.ICU, now, self.config.icu_stay)
        elif roll < p_icu + p_ward:
            self.move_or_board(admission, Unit.UnitType.WARD, now, self.config.ward_stay)
        else:
            services.discharge_patient(admission=admission, outcome=Admission.Outcome.HOME, discharged_at=now)

    def finish_icu_stay(self, admission, now, decide):
        if decide.random() < self.config.icu_mortality:
            services.discharge_patient(admission=admission, outcome=Admission.Outcome.DECEASED, discharged_at=now)
        elif decide.random() < self.config.icu_step_down_probability:
            self.move_or_board(admission, Unit.UnitType.WARD, now, self.config.ward_stay)
        else:
            services.discharge_patient(admission=admission, outcome=Admission.Outcome.HOME, discharged_at=now)

    def finish_ward_stay(self, admission, now, decide):
        outcome = (
            Admission.Outcome.DECEASED if decide.random() < self.config.ward_mortality else Admission.Outcome.HOME
        )
        services.discharge_patient(admission=admission, outcome=outcome, discharged_at=now)

    def move_or_board(self, admission, unit_type, now, stay):
        bed = self.free_bed(unit_type)
        if bed is None:
            # "Boarding": no bed free, so the patient stays where they are and we try again later.
            admission.expected_discharge_at = now + timedelta(minutes=self.config.boarding_retry_minutes)
            admission.save(update_fields=["expected_discharge_at"])
            return
        services.transfer_patient(
            admission=admission, to_bed=bed, transferred_at=now, expected_discharge_at=now + self.stay(stay)
        )

    def clean_beds(self, now):
        for bed in Bed.objects.filter(status=Bed.Status.CLEANING):
            if bed.status_since is None:
                services.mark_bed_clean(bed=bed, at=now)
                continue
            duration = np.random.default_rng(
                [self.seed, bed.pk, int(bed.status_since.timestamp())]
            ).uniform(*self.config.cleaning_minutes)
            if now >= bed.status_since + timedelta(minutes=duration):
                services.mark_bed_clean(bed=bed, at=now)

    # ---------- helpers ----------

        # ---------- saving readings ----------

    def save_vitals(self, admission, recorded_at, values):
        if self.history:
            self.vital_buffer.append(VitalReading(admission=admission, recorded_at=recorded_at, **values))
        else:
            services.record_vitals(admission=admission, recorded_at=recorded_at, **values)

    def save_telemetry(self, equipment, recorded_at, values):
        if self.history:
            self.telemetry_buffer.append(EquipmentReading(equipment=equipment, recorded_at=recorded_at, **values))
        else:
            equipment_services.record_telemetry(equipment=equipment, recorded_at=recorded_at, **values)

    def flush(self):
        """Save everything in the baskets to the database, thousands of rows at a time."""
        VitalReading.objects.bulk_create(self.vital_buffer, batch_size=5000)
        EquipmentReading.objects.bulk_create(self.telemetry_buffer, batch_size=5000)
        self.vital_buffer.clear()
        self.telemetry_buffer.clear()

    def decision_rng(self, admission, unit_type):
        """Random numbers fixed per admission and stage, so retries give the same decision."""
        return np.random.default_rng([self.seed, admission.pk, STAGE[unit_type]])

    def stay(self, median_and_spread):
        median, spread = median_and_spread
        return timedelta(hours=float(self.rng.lognormal(math.log(median), spread)))

    def free_bed(self, unit_type):
        beds = list(
            Bed.objects.filter(unit__unit_type=unit_type, is_active=True, status=Bed.Status.FREE).order_by("code")
        )
        return beds[self.rng.integers(len(beds))] if beds else None

    def new_patient(self, now):
        sex = str(self.rng.choice(["M", "F"]))
        first_name = self.fake.first_name_male() if sex == "M" else self.fake.first_name_female()
        age = float(np.clip(self.rng.normal(58, 18), 18, 98))
        birth_date = (timezone.localtime(now) - timedelta(days=age * 365.25)).date()
        return Patient.objects.create(
            first_name=first_name, last_name=self.fake.last_name(), sex=sex, date_of_birth=birth_date
        )
