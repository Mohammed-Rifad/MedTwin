from datetime import date, timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from equipment import services as equipment_services
from equipment.models import Equipment
from hospital import services
from hospital.models import Bed, Patient, Unit

from .models import Alert


def make_patient(name="Ravi"):
    return Patient.objects.create(first_name=name, last_name="Kumar", date_of_birth=date(1960, 1, 1), sex="M")


class VitalAlertTests(TestCase):
    def setUp(self):
        ward = Unit.objects.create(name="Ward", code="W", unit_type=Unit.UnitType.WARD)
        for number in range(1, 11):  # 10 beds, so one patient never triggers an occupancy alert
            Bed.objects.create(unit=ward, code=f"W-{number:02d}")
        self.admission = services.admit_patient(patient=make_patient(), bed=Bed.objects.get(code="W-01"))
        self.start = timezone.now()

    def record(self, minutes, **values):
        return services.record_vitals(
            admission=self.admission, recorded_at=self.start + timedelta(minutes=minutes), **values
        )

    def spo2_alerts(self):
        return Alert.objects.filter(kind=Alert.Kind.LOW_SPO2)

    def test_one_alert_for_a_lasting_problem(self):
        for step, spo2 in enumerate([90, 89, 90, 88]):
            self.record(step * 15, spo2=spo2)
        alert = self.spo2_alerts().get()  # .get() fails if there isn't exactly one
        self.assertEqual(alert.value, 88)
        self.assertIn("Ravi Kumar (W-01)", alert.message)

    def test_escalates_but_never_downgrades(self):
        self.record(0, spo2=90)
        self.record(15, spo2=85)
        self.record(30, spo2=90)
        alert = self.spo2_alerts().get()
        self.assertEqual(alert.severity, Alert.Severity.CRITICAL)
        self.assertEqual(alert.value, 90)

    def test_closes_only_after_the_clear_line(self):
        self.record(0, spo2=89)
        self.record(15, spo2=93)  # better, but still inside the gap
        self.assertEqual(self.spo2_alerts().get().status, Alert.Status.OPEN)
        self.record(30, spo2=96)  # past the clear line (94)
        self.assertEqual(self.spo2_alerts().get().status, Alert.Status.RESOLVED)

    def test_new_alert_after_the_previous_one_was_resolved(self):
        self.record(0, spo2=89)
        self.record(15, spo2=96)
        self.record(30, spo2=89)
        self.assertEqual(self.spo2_alerts().count(), 2)
        self.assertEqual(self.spo2_alerts().exclude(status=Alert.Status.RESOLVED).count(), 1)

    def test_discharge_closes_the_patients_alerts(self):
        self.record(0, spo2=85, respiratory_rate=32)
        services.discharge_patient(admission=self.admission, outcome="HOME")
        active = Alert.objects.filter(admission=self.admission).exclude(status=Alert.Status.RESOLVED)
        self.assertFalse(active.exists())

    def test_database_blocks_duplicate_active_alerts(self):
        self.record(0, spo2=89)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Alert.objects.create(
                kind=Alert.Kind.LOW_SPO2, subject=f"admission:{self.admission.pk}",
                severity=Alert.Severity.WARNING, message="duplicate",
            )


class UnitAndEquipmentAlertTests(TestCase):
    def test_full_unit_is_critical_then_clears(self):
        icu = Unit.objects.create(name="ICU", code="ICU", unit_type=Unit.UnitType.ICU)
        beds = [Bed.objects.create(unit=icu, code=f"ICU-0{number}") for number in range(1, 5)]
        admissions = [
            services.admit_patient(patient=make_patient(f"P{number}"), bed=bed)
            for number, bed in enumerate(beds)
        ]
        alert = Alert.objects.get(kind=Alert.Kind.HIGH_OCCUPANCY)
        self.assertEqual(alert.severity, Alert.Severity.CRITICAL)  # 4 of 4 beds = 100%
        for admission in admissions[:2]:
            services.discharge_patient(admission=admission, outcome="HOME")  # down to 2 of 4 = 50%
        alert.refresh_from_db()
        self.assertEqual(alert.status, Alert.Status.RESOLVED)

    def test_overheating_then_failure_then_repair(self):
        vent = Equipment.objects.create(code="VENT-01", kind=Equipment.Kind.VENTILATOR)
        equipment_services.record_telemetry(equipment=vent, temperature=45, running_hours=10)
        self.assertEqual(Alert.objects.get(kind=Alert.Kind.EQUIPMENT_OVERHEATING).severity, Alert.Severity.WARNING)

        equipment_services.mark_failed(equipment=vent)
        self.assertTrue(Alert.objects.filter(kind=Alert.Kind.EQUIPMENT_FAILURE, status=Alert.Status.OPEN).exists())

        equipment_services.start_maintenance(equipment=vent, reason="Repair")
        equipment_services.finish_maintenance(equipment=vent)
        self.assertFalse(Alert.objects.exclude(status=Alert.Status.RESOLVED).exists())
