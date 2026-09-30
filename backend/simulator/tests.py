from django.core.management import CommandError, call_command
from django.test import TestCase
from dataclasses import replace
from datetime import timedelta
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from equipment.models import Equipment
from hospital import services
from hospital.models import Admission, Bed, EmergencyArrival, Patient, Unit

from .config import SimulationConfig
from .engine import Simulator

from accounts.models import User
from equipment.models import Equipment
from hospital.models import Bed, Unit


class SeedHospitalTests(TestCase):
    def seed(self, *args):
        call_command("seed_hospital", *args, stdout=open("nul", "w"))

    def test_creates_demo_hospital(self):
        self.seed()
        self.assertEqual(Unit.objects.count(), 4)
        self.assertEqual(Bed.objects.count(), 52)
        self.assertFalse(Bed.objects.exclude(status=Bed.Status.FREE).exists())
        self.assertEqual(Equipment.objects.count(), 30)
        self.assertEqual(User.objects.get(username="demo_doctor").role, User.Role.DOCTOR)

    def test_refuses_to_seed_twice_without_reset(self):
        self.seed()
        with self.assertRaises(CommandError):
            self.seed()

    def test_reset_rebuilds_the_same_hospital(self):
        self.seed()
        self.seed("--reset")
        self.assertEqual(Bed.objects.count(), 52)
        self.assertEqual(Equipment.objects.count(), 30)

    def test_beds_are_inside_their_unit_on_the_map(self):
        self.seed()
        for bed in Bed.objects.select_related("unit"):
            unit = bed.unit
            self.assertTrue(unit.map_x < bed.map_x < unit.map_x + unit.map_width, bed.code)
            self.assertTrue(unit.map_y < bed.map_y < unit.map_y + unit.map_height, bed.code)

class SimulatorTests(TestCase):
    def setUp(self):
        call_command("seed_hospital", stdout=StringIO())
        self.now = timezone.now()

    def simulator(self, **overrides):
        return Simulator(config=replace(SimulationConfig(), **overrides), seed=1)

    def test_busy_hour_fills_ed_and_extra_patients_wait(self):
        simulator = self.simulator(ed_arrivals_per_hour=100, elective_admissions_per_day=0)
        simulator.step(self.now, hours=1)
        ed = Unit.objects.get(code="ED")
        self.assertEqual(ed.occupied_count, ed.capacity)
        self.assertTrue(EmergencyArrival.objects.filter(status=EmergencyArrival.Status.WAITING).exists())

    def test_critical_patient_moves_from_ed_to_icu(self):
        simulator = self.simulator(ed_disposition={level: (1.0, 0.0) for level in range(1, 6)})
        arrival = EmergencyArrival.objects.create(
            patient=simulator.new_patient(self.now), triage_level=1,
            complaint="Cardiac arrest", arrived_at=self.now,
        )
        simulator.move_ed_queue_into_bays(self.now)
        later = self.now + timedelta(hours=48)
        simulator.process_due_admissions(later)
        admission = Admission.objects.get(patient=arrival.patient)
        self.assertEqual(admission.bed.unit.code, "ICU")
        self.assertGreater(admission.expected_discharge_at, later)

    def test_discharged_bed_is_cleaned_then_freed(self):
        simulator = self.simulator(ward_mortality=0.0)
        bed = Bed.objects.filter(unit__code="WA").first()
        services.admit_patient(
            patient=simulator.new_patient(self.now), bed=bed,
            admitted_at=self.now, expected_discharge_at=self.now + timedelta(hours=1),
        )
        simulator.process_due_admissions(self.now + timedelta(hours=2))
        bed.refresh_from_db()
        self.assertEqual(bed.status, Bed.Status.CLEANING)
        simulator.clean_beds(self.now + timedelta(hours=4))
        bed.refresh_from_db()
        self.assertEqual(bed.status, Bed.Status.FREE)

    def test_same_seed_gives_same_patients(self):
        runs = []
        for _ in range(2):
            call_command("seed_hospital", "--reset", stdout=StringIO())
            Simulator(seed=7).step(self.now, hours=6)
            runs.append(sorted(Patient.objects.values_list("first_name", "last_name")))
        self.assertTrue(runs[0])
        self.assertEqual(runs[0], runs[1])
