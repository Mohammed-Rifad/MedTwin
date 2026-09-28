from datetime import date

from django.db.models import ProtectedError
from django.test import TestCase

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
