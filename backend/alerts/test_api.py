from datetime import date
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from hospital import services as hospital_services
from hospital.models import Bed, Patient, Unit

from .models import Alert
from .services import raise_alert


class AlertActionTests(APITestCase):
    def setUp(self):
        self.nurse = User.objects.create_user(username="nurse1", password="x", role=User.Role.NURSE)
        self.doctor = User.objects.create_user(username="doc1", password="x", role=User.Role.DOCTOR)
        self.alert = raise_alert(
            kind=Alert.Kind.LOW_SPO2, subject="admission:1", severity=Alert.Severity.WARNING,
            message="SpO₂ 89% (≤ 91%)", value=89,
        )

    def post(self, action):
        return self.client.post(reverse(f"alerts:alerts-{action}", args=[self.alert.pk]))

    def test_acknowledge_records_who_and_only_works_once(self):
        self.client.force_authenticate(self.nurse)
        response = self.post("acknowledge")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Alert.Status.ACKNOWLEDGED)
        self.assertEqual(response.data["acknowledged_by"], "nurse1")
        self.assertIsNotNone(response.data["acknowledged_at"])
        self.assertEqual(self.post("acknowledge").status_code, status.HTTP_400_BAD_REQUEST)

    def test_resolve_records_who_and_only_works_once(self):
        self.client.force_authenticate(self.doctor)
        response = self.post("resolve")
        self.assertEqual(response.data["status"], Alert.Status.RESOLVED)
        self.assertEqual(response.data["resolved_by"], "doc1")
        self.assertEqual(self.post("resolve").status_code, status.HTTP_400_BAD_REQUEST)

    def test_active_filter(self):
        self.client.force_authenticate(self.nurse)
        url = reverse("alerts:alerts-list")
        self.assertEqual(self.client.get(url, {"active": "true"}).data["count"], 1)
        self.post("resolve")
        self.assertEqual(self.client.get(url, {"active": "true"}).data["count"], 0)
        self.assertEqual(self.client.get(url, {"active": "false"}).data["count"], 1)

    def test_login_required(self):
        response = self.client.get(reverse("alerts:alerts-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@patch("twin.broadcast._send")
class LiveAlertTests(APITestCase):
    def sent(self, send, event_type):
        return [call.args[0]["data"] for call in send.call_args_list if call.args[0]["type"] == event_type]

    def test_new_worse_and_resolved_alerts_are_announced_but_repeats_are_not(self, send):
        def low_spo2(value, severity):
            return raise_alert(
                kind=Alert.Kind.LOW_SPO2, subject="admission:1", severity=severity,
                message=f"SpO₂ {value}%", value=value,
            )

        with self.captureOnCommitCallbacks(execute=True):
            alert = low_spo2(90, Alert.Severity.WARNING)   # new: announced
            low_spo2(89, Alert.Severity.WARNING)            # same problem, same severity: quiet
            low_spo2(85, Alert.Severity.CRITICAL)           # got worse: announced
            nurse = User.objects.create_user(username="nurse1", password="x", role=User.Role.NURSE)
            self.client.force_authenticate(nurse)
            self.client.post(reverse("alerts:alerts-acknowledge", args=[alert.pk]))  # announced

        updates = self.sent(send, "alert_update")
        self.assertEqual(
            [(update["severity"], update["status"]) for update in updates],
            [("WARNING", "OPEN"), ("CRITICAL", "OPEN"), ("CRITICAL", "ACKNOWLEDGED")],
        )


class ThresholdTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin1", password="x", role=User.Role.ADMIN)
        self.nurse = User.objects.create_user(username="nurse1", password="x", role=User.Role.NURSE)
        self.client.force_authenticate(self.admin)

    def url(self, key=None, action=None):
        if key is None:
            return reverse("alerts:thresholds-list")
        if action is None:
            return reverse("alerts:thresholds-detail", args=[key])
        return reverse(f"alerts:thresholds-{action}", args=[key])

    def test_only_admins_can_see_limits(self):
        self.client.force_authenticate(self.nurse)
        self.assertEqual(self.client.get(self.url()).status_code, status.HTTP_403_FORBIDDEN)

    def test_lists_every_rule_with_defaults(self):
        rules = {rule["key"]: rule for rule in self.client.get(self.url()).data}
        self.assertEqual(rules["spo2"]["warning"], 91)
        self.assertTrue(rules["spo2"]["is_default"])
        self.assertIn("equipment_temperature:VENTILATOR", rules)

    def test_changed_limit_is_used_for_new_readings(self):
        response = self.client.patch(self.url("spo2"), {"warning": 93, "clear": 95}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_default"])
        self.assertEqual(response.data["updated_by"], "admin1")

        ward = Unit.objects.create(name="Ward", code="W", unit_type=Unit.UnitType.WARD)
        for number in range(1, 11):
            Bed.objects.create(unit=ward, code=f"W-{number:02d}")
        patient = Patient.objects.create(first_name="Ravi", last_name="Kumar", date_of_birth=date(1960, 1, 1), sex="M")
        admission = hospital_services.admit_patient(patient=patient, bed=Bed.objects.get(code="W-01"))
        hospital_services.record_vitals(admission=admission, spo2=92)  # fine before, low now
        self.assertTrue(Alert.objects.filter(kind=Alert.Kind.LOW_SPO2).exists())

    def test_limits_in_the_wrong_order_are_refused(self):
        # For SpO₂ (danger is "below"), the clear line must be above the warning line.
        response = self.client.patch(self.url("spo2"), {"warning": 91, "clear": 90}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_goes_back_to_default(self):
        self.client.patch(self.url("heart_rate"), {"warning": 110, "clear": 100}, format="json")
        response = self.client.post(self.url("heart_rate", "reset"))
        self.assertEqual(response.data["warning"], 120)
        self.assertTrue(response.data["is_default"])

    def test_unknown_rule_is_not_found(self):
        self.assertEqual(self.client.get(self.url("nonsense")).status_code, status.HTTP_404_NOT_FOUND)
