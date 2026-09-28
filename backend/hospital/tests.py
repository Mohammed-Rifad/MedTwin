from datetime import date

from django.db.models import ProtectedError
from django.test import TestCase
from datetime import date

from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from .models import Admission, Bed, EmergencyArrival, Patient, Unit
from .services import (
    HospitalError,
    admit_patient,
    discharge_patient,
    mark_bed_clean,
    record_vitals,
    transfer_patient,
)

from .models import Bed, Patient, Unit


class UnitTests(TestCase):
    def setUp(self):
        self.icu = Unit.objects.create(name="ICU", code="ICU", unit_type=Unit.UnitType.ICU)
        Bed.objects.create(unit=self.icu, code="ICU-01", status=Bed.Status.OCCUPIED)
        Bed.objects.create(unit=self.icu, code="ICU-02")
        Bed.objects.create(unit=self.icu, code="ICU-03", is_active=False)

    def test_capacity_counts_only_active_beds(self):
        self.assertEqual(self.icu.capacity, 2)

    def test_occupied_count(self):
        self.assertEqual(self.icu.occupied_count, 1)

    def test_unit_with_beds_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.icu.delete()


class PatientTests(TestCase):
    def make_patient(self, **kwargs):
        data = {"first_name": "Test", "last_name": "Patient", "date_of_birth": date(1970, 1, 1), "sex": "M"}
        data.update(kwargs)
        return Patient.objects.create(**data)

    def test_mrn_is_generated_and_unique(self):
        first = self.make_patient()
        second = self.make_patient()
        self.assertTrue(first.mrn.startswith("MRN-"))
        self.assertNotEqual(first.mrn, second.mrn)

    def test_age_from_date_of_birth(self):
        born_jan_first = date(date.today().year - 50, 1, 1)
        patient = self.make_patient(date_of_birth=born_jan_first)
        self.assertEqual(patient.age, 50)

class AdmissionServiceTests(TestCase):
    def setUp(self):
        icu = Unit.objects.create(name="ICU", code="ICU", unit_type=Unit.UnitType.ICU)
        self.bed1 = Bed.objects.create(unit=icu, code="ICU-01")
        self.bed2 = Bed.objects.create(unit=icu, code="ICU-02")
        self.patient = Patient.objects.create(
            first_name="Ravi", last_name="Kumar", date_of_birth=date(1958, 3, 12), sex="M"
        )
        self.other_patient = Patient.objects.create(
            first_name="Anita", last_name="Das", date_of_birth=date(1970, 6, 1), sex="F"
        )

    def assertBedStatus(self, bed, status):
        bed.refresh_from_db()
        self.assertEqual(bed.status, status)

    def test_admit_marks_bed_occupied(self):
        admit_patient(patient=self.patient, bed=self.bed1)
        self.assertBedStatus(self.bed1, Bed.Status.OCCUPIED)

    def test_cannot_admit_into_occupied_bed(self):
        admit_patient(patient=self.patient, bed=self.bed1)
        with self.assertRaises(HospitalError):
            admit_patient(patient=self.other_patient, bed=self.bed1)

    def test_cannot_admit_same_patient_twice(self):
        admit_patient(patient=self.patient, bed=self.bed1)
        with self.assertRaises(HospitalError):
            admit_patient(patient=self.patient, bed=self.bed2)

    def test_database_blocks_two_active_admissions_in_one_bed(self):
        admit_patient(patient=self.patient, bed=self.bed1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Admission.objects.create(patient=self.other_patient, bed=self.bed1)

    def test_transfer_moves_patient_and_records_it(self):
        admission = admit_patient(patient=self.patient, bed=self.bed1)
        transfer_patient(admission=admission, to_bed=self.bed2)
        admission.refresh_from_db()
        self.assertEqual(admission.bed, self.bed2)
        self.assertEqual(admission.transfers.count(), 1)
        self.assertBedStatus(self.bed1, Bed.Status.CLEANING)
        self.assertBedStatus(self.bed2, Bed.Status.OCCUPIED)

    def test_discharge_then_clean_frees_bed(self):
        admission = admit_patient(patient=self.patient, bed=self.bed1)
        discharge_patient(admission=admission, outcome=Admission.Outcome.HOME)
        self.assertBedStatus(self.bed1, Bed.Status.CLEANING)
        mark_bed_clean(bed=self.bed1)
        self.assertBedStatus(self.bed1, Bed.Status.FREE)

    def test_admission_from_emergency_updates_arrival(self):
        arrival = EmergencyArrival.objects.create(
            patient=self.patient, triage_level=2, complaint="Chest pain"
        )
        admission = admit_patient(patient=self.patient, bed=self.bed1, emergency_arrival=arrival)
        arrival.refresh_from_db()
        self.assertEqual(arrival.status, EmergencyArrival.Status.ADMITTED)
        self.assertEqual(arrival.admission, admission)

    def test_vitals_rejected_after_discharge(self):
        admission = admit_patient(patient=self.patient, bed=self.bed1)
        discharge_patient(admission=admission, outcome=Admission.Outcome.HOME)
        with self.assertRaises(HospitalError):
            record_vitals(admission=admission, heart_rate=80)

    def test_impossible_vital_value_rejected(self):
        admission = admit_patient(patient=self.patient, bed=self.bed1)
        with self.assertRaises(Exception):
            record_vitals(admission=admission, heart_rate=900)
