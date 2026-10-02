from io import StringIO

from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from equipment.models import Equipment
from hospital import services
from hospital.models import Bed, EmergencyArrival
from twin.models import HospitalClock

from .engine import Simulator
from .models import InjectedFault


class SimulatorApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_hospital", stdout=StringIO())
        cls.admin = User.objects.get(username="demo_admin")
        cls.nurse = User.objects.get(username="demo_nurse")

    def setUp(self):
        self.client.force_authenticate(self.admin)

    def test_only_admin_can_use_the_controls(self):
        self.client.force_authenticate(self.nurse)
        response = self.client.get(reverse("simulator:status"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_start_and_pause(self):
        started = self.client.post(reverse("simulator:start"), {"speed": 120}, format="json")
        self.assertTrue(started.data["running"])
        self.assertEqual(started.data["speed"], 120)
        paused = self.client.post(reverse("simulator:pause"))
        self.assertFalse(paused.data["running"])
        self.assertFalse(HospitalClock.load().running)

    def test_surge_adds_emergency_patients(self):
        response = self.client.post(reverse("simulator:surge"), {"patients": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(EmergencyArrival.objects.count(), 5)

    def test_deteriorate_and_device_fault(self):
        bed = Bed.objects.filter(unit__code="WA").first()
        patient = Simulator(seed=1).new_patient(HospitalClock.load().now())
        admission = services.admit_patient(patient=patient, bed=bed)

        response = self.client.post(reverse("simulator:deteriorate"), {"admission": admission.pk}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        admission.refresh_from_db()
        self.assertIsNotNone(admission.physiology.deterioration_onset_at)

        vent = Equipment.objects.get(code="VENT-01")
        url = reverse("simulator:device-fault")
        first = self.client.post(url, {"equipment": vent.pk}, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InjectedFault.objects.filter(equipment=vent).count(), 1)
        second = self.client.post(url, {"equipment": vent.pk}, format="json")
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
