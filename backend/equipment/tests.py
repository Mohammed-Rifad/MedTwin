from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User

from . import services
from .models import Equipment


class MaintenanceApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin1", password="x", role=User.Role.ADMIN)
        self.nurse = User.objects.create_user(username="nurse1", password="x", role=User.Role.NURSE)
        self.vent = Equipment.objects.create(code="VENT-01", kind=Equipment.Kind.VENTILATOR)

    def post(self, name, data=None):
        return self.client.post(reverse(f"equipment:{name}", args=[self.vent.pk]), data or {}, format="json")

    def test_nurse_cannot_start_maintenance(self):
        self.client.force_authenticate(self.nurse)
        self.assertEqual(
            self.post("equipment-start-maintenance", {"reason": "Check"}).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_maintenance_cycle(self):
        self.client.force_authenticate(self.admin)
        started = self.post("equipment-start-maintenance", {"reason": "Temperature rising"})
        self.assertEqual(started.status_code, status.HTTP_200_OK)
        self.assertEqual(started.data["status"], Equipment.Status.MAINTENANCE)
        self.assertEqual(started.data["open_maintenance"]["reason"], "Temperature rising")

        again = self.post("equipment-start-maintenance", {"reason": "Again"})
        self.assertEqual(again.status_code, status.HTTP_400_BAD_REQUEST)

        finished = self.post("equipment-finish-maintenance", {"notes": "Fan replaced"})
        self.assertEqual(finished.data["status"], Equipment.Status.OK)
        self.assertIsNone(finished.data["open_maintenance"])
        self.assertIsNotNone(finished.data["last_serviced_at"])

    def test_status_cannot_be_edited_directly(self):
        self.client.force_authenticate(self.admin)
        self.client.patch(
            reverse("equipment:equipment-detail", args=[self.vent.pk]), {"status": "FAULT"}, format="json"
        )
        self.vent.refresh_from_db()
        self.assertEqual(self.vent.status, Equipment.Status.OK)

    def test_no_telemetry_while_in_maintenance(self):
        services.start_maintenance(equipment=self.vent, reason="Service")
        self.vent.refresh_from_db()
        with self.assertRaises(services.EquipmentError):
            services.record_telemetry(equipment=self.vent, temperature=40, running_hours=100)
