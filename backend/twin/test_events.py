from datetime import date
from unittest.mock import patch

from django.db import transaction
from django.test import TestCase

from equipment import services as equipment_services
from equipment.models import Equipment
from hospital import services
from hospital.models import Bed, Patient, Unit

from .broadcast import muted


@patch("twin.broadcast._send")
class LiveEventTests(TestCase):
    def setUp(self):
        icu = Unit.objects.create(name="ICU", code="ICU", unit_type=Unit.UnitType.ICU)
        self.bed = Bed.objects.create(unit=icu, code="ICU-01")
        Bed.objects.create(unit=icu, code="ICU-02")  # so one admission doesn't fill the unit
        self.patient = Patient.objects.create(
            first_name="Ravi", last_name="Kumar", date_of_birth=date(1960, 1, 1), sex="M"
        )

    def sent_types(self, send):
        return [call.args[0]["type"] for call in send.call_args_list]

    def test_admission_announces_bed_and_admission(self, send):
        with self.captureOnCommitCallbacks(execute=True):
            services.admit_patient(patient=self.patient, bed=self.bed)
        self.assertEqual(self.sent_types(send), ["bed_update", "admission_update"])
        self.assertEqual(send.call_args_list[0].args[0]["data"]["status"], "OCCUPIED")

    def test_nothing_announced_if_save_fails(self, send):
        with self.captureOnCommitCallbacks(execute=True):
            try:
                with transaction.atomic():
                    services.admit_patient(patient=self.patient, bed=self.bed)
                    raise RuntimeError("save failed")
            except RuntimeError:
                pass
        send.assert_not_called()

    def test_nothing_announced_when_muted(self, send):
        with self.captureOnCommitCallbacks(execute=True), muted():
            services.admit_patient(patient=self.patient, bed=self.bed)
        send.assert_not_called()

    def test_vitals_and_equipment_are_announced(self, send):
        vent = Equipment.objects.create(code="VENT-01", kind=Equipment.Kind.VENTILATOR)
        with self.captureOnCommitCallbacks(execute=True):
            admission = services.admit_patient(patient=self.patient, bed=self.bed)
            services.record_vitals(admission=admission, heart_rate=90)
            equipment_services.start_maintenance(equipment=vent, reason="Check")
        self.assertIn("vitals", self.sent_types(send))
        self.assertIn("equipment_update", self.sent_types(send))
