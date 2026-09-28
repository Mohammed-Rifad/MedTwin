from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import AuditLog, User

from . import services
from .models import Bed, EmergencyArrival, Patient, Unit


class HospitalApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin1", password="x", role=User.Role.ADMIN)
        self.doctor = User.objects.create_user(username="doc1", password="x", role=User.Role.DOCTOR)
        self.nurse = User.objects.create_user(username="nurse1", password="x", role=User.Role.NURSE)
        icu = Unit.objects.create(name="ICU", code="ICU", unit_type=Unit.UnitType.ICU)
        self.bed1 = Bed.objects.create(unit=icu, code="ICU-01")
        self.bed2 = Bed.objects.create(unit=icu, code="ICU-02")
        self.patient = self.make_patient("Ravi", "Kumar")

    def make_patient(self, first_name, last_name):
        return Patient.objects.create(
            first_name=first_name, last_name=last_name, date_of_birth=date(1960, 1, 1), sex="M"
        )

    def as_user(self, user):
        self.client.force_authenticate(user)

    def test_nurse_registers_patient_but_doctor_cannot(self):
        url = reverse("hospital:patients-list")
        payload = {"first_name": "Anita", "last_name": "Das", "date_of_birth": "1970-06-01", "sex": "F"}
        self.as_user(self.doctor)
        self.assertEqual(self.client.post(url, payload, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.as_user(self.nurse)
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["mrn"].startswith("MRN-"))

    def test_admit_via_api_occupies_bed(self):
        self.as_user(self.nurse)
        response = self.client.post(
            reverse("hospital:admissions-list"),
            {"patient": self.patient.pk, "bed": self.bed1.pk, "reason": "Pneumonia"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.bed1.refresh_from_db()
        self.assertEqual(self.bed1.status, Bed.Status.OCCUPIED)

    def test_admit_into_occupied_bed_returns_clear_error(self):
        services.admit_patient(patient=self.patient, bed=self.bed1)
        other = self.make_patient("Anita", "Das")
        self.as_user(self.nurse)
        response = self.client.post(
            reverse("hospital:admissions-list"), {"patient": other.pk, "bed": self.bed1.pk}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not free", response.data["detail"])

    def test_only_doctor_can_discharge(self):
        admission = services.admit_patient(patient=self.patient, bed=self.bed1)
        url = reverse("hospital:admissions-discharge", args=[admission.pk])
        self.as_user(self.nurse)
        self.assertEqual(
            self.client.post(url, {"outcome": "HOME"}, format="json").status_code, status.HTTP_403_FORBIDDEN
        )
        self.as_user(self.doctor)
        response = self.client.post(url, {"outcome": "HOME"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["outcome"], "HOME")

    def test_nurse_records_vitals_and_impossible_values_are_rejected(self):
        admission = services.admit_patient(patient=self.patient, bed=self.bed1)
        url = reverse("hospital:admissions-vitals", args=[admission.pk])
        self.as_user(self.nurse)
        ok = self.client.post(url, {"heart_rate": 118, "spo2": 90}, format="json")
        self.assertEqual(ok.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ok.data["source"], "MANUAL")
        bad = self.client.post(url, {"heart_rate": 900}, format="json")
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.get(url).data["count"], 1)

    def test_viewing_patient_record_is_audited(self):
        self.as_user(self.doctor)
        response = self.client.get(reverse("hospital:patients-detail", args=[self.patient.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            AuditLog.objects.filter(
                user=self.doctor, action=AuditLog.Action.VIEW, object_id=str(self.patient.pk)
            ).exists()
        )

    def test_filter_admitted_patients_and_search_by_mrn(self):
        services.admit_patient(patient=self.patient, bed=self.bed1)
        self.make_patient("Anita", "Das")
        self.as_user(self.nurse)
        url = reverse("hospital:patients-list")
        admitted = self.client.get(url, {"admitted": "true"})
        self.assertEqual(admitted.data["count"], 1)
        self.assertEqual(admitted.data["results"][0]["current_admission"]["bed"], "ICU-01")
        found = self.client.get(url, {"search": self.patient.mrn})
        self.assertEqual(found.data["count"], 1)

    def test_emergency_queue_is_ordered_by_triage_and_admits(self):
        EmergencyArrival.objects.create(
            patient=self.make_patient("Anita", "Das"), triage_level=4, complaint="Sprained ankle"
        )
        urgent = EmergencyArrival.objects.create(patient=self.patient, triage_level=1, complaint="Cardiac arrest")
        self.as_user(self.nurse)
        queue = self.client.get(reverse("hospital:emergency-list"), {"status": "WAITING"})
        self.assertEqual(queue.data["results"][0]["id"], urgent.pk)
        response = self.client.post(
            reverse("hospital:emergency-admit", args=[urgent.pk]), {"bed": self.bed1.pk}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        urgent.refresh_from_db()
        self.assertEqual(urgent.status, EmergencyArrival.Status.ADMITTED)

    def test_units_show_capacity_and_only_admin_can_create(self):
        services.admit_patient(patient=self.patient, bed=self.bed1)
        url = reverse("hospital:units-list")
        self.as_user(self.nurse)
        unit = self.client.get(url).data["results"][0]
        self.assertEqual((unit["capacity"], unit["occupied"]), (2, 1))
        payload = {"name": "Ward A", "code": "WA", "unit_type": "WARD"}
        self.assertEqual(self.client.post(url, payload, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.as_user(self.admin)
        self.assertEqual(self.client.post(url, payload, format="json").status_code, status.HTTP_201_CREATED)
