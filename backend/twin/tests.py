from datetime import date, timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from alerts.services import raise_alert
from equipment import services as equipment_services
from equipment.models import Equipment
from hospital import services
from hospital.models import Bed, EmergencyArrival, Patient

from .models import HospitalClock


class HospitalClockTests(TestCase):
    def test_follows_real_time_until_started(self):
        self.assertLess(abs(HospitalClock.load().now() - timezone.now()), timedelta(seconds=1))

    def test_runs_faster_than_real_time(self):
        start = timezone.now()
        clock = HospitalClock.load()
        clock.anchor_sim_time = start
        clock.anchor_real_time = timezone.now() - timedelta(seconds=10)
        clock.speed = 60
        clock.running = True
        clock.save()
        elapsed = clock.now() - start
        self.assertGreaterEqual(elapsed, timedelta(minutes=10))
        self.assertLess(elapsed, timedelta(minutes=11))

    def test_pause_freezes_time(self):
        clock = HospitalClock.load()
        clock.start(speed=3600)
        clock.pause()
        self.assertEqual(clock.now(), clock.now())


class SummaryTests(TestCase):
    def test_summary_counts_the_hospital(self):
        call_command("seed_hospital", stdout=StringIO())
        patient = Patient.objects.create(first_name="Ravi", last_name="Kumar", date_of_birth=date(1960, 1, 1), sex="M")
        services.admit_patient(patient=patient, bed=Bed.objects.get(code="ICU-01"))
        EmergencyArrival.objects.create(patient=patient, triage_level=2, complaint="Chest pain")
        raise_alert(kind="LOW_SPO2", subject="test:1", severity="CRITICAL", message="SpO2 85%")
        equipment_services.mark_failed(equipment=Equipment.objects.get(code="VENT-01"))

        client = APIClient()
        client.force_authenticate(User.objects.get(username="demo_nurse"))
        data = client.get("/api/twin/summary/").data

        self.assertEqual(data["icu"], {"occupied": 1, "capacity": 12, "percent": 8})
        self.assertEqual(data["beds"]["occupied"], 1)
        self.assertEqual(data["emergency"]["waiting"], 1)
        self.assertEqual(data["emergency"]["by_triage"], {2: 1})
        self.assertEqual(data["alerts"]["by_severity"]["CRITICAL"], 2)  # the test alert + the ventilator failure
        self.assertEqual(data["equipment"]["by_status"]["FAULT"], 1)
        self.assertEqual(data["today"]["admissions"], 1)
