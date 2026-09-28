from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import AuditLog, User



class AuthTests(APITestCase):
    def setUp(self):
        self.password = "Str0ng-pass-123"
        User.objects.create_user(
            username="nurse1", password=self.password, role=User.Role.NURSE
        )

    def login(self, password=None):
        return self.client.post(
            reverse("accounts:login"),
            {"username": "nurse1", "password": password or self.password},
            format="json",
        )

    def test_login_returns_tokens(self):
        response = self.login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_with_wrong_password_fails(self):
        response = self.login(password="wrong-password")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_role(self):
        token = self.login().data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(reverse("accounts:me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], User.Role.NURSE)

    def test_me_requires_token(self):
        response = self.client.get(reverse("accounts:me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_blacklists_refresh_token(self):
        refresh = self.login().data["refresh"]
        logout = self.client.post(
            reverse("accounts:logout"), {"refresh": refresh}, format="json"
        )
        self.assertEqual(logout.status_code, status.HTTP_200_OK)
        again = self.client.post(
            reverse("accounts:refresh"), {"refresh": refresh}, format="json"
        )
        self.assertEqual(again.status_code, status.HTTP_401_UNAUTHORIZED)


class StaffManagementTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin1", password="Adm1n-pass-123", role=User.Role.ADMIN
        )
        self.nurse = User.objects.create_user(
            username="nurse1", password="Nurs3-pass-123", role=User.Role.NURSE
        )

    def test_nurse_cannot_list_staff(self):
        self.client.force_authenticate(self.nurse)
        response = self.client.get(reverse("accounts:users-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_creates_staff_with_hashed_password(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse("accounts:users-list"),
            {"username": "doc1", "password": "D0ctor-pass-123", "role": "DOCTOR"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)
        doctor = User.objects.get(username="doc1")
        self.assertTrue(doctor.check_password("D0ctor-pass-123"))
        self.assertTrue(
            AuditLog.objects.filter(action=AuditLog.Action.CREATE, object_id=str(doctor.pk)).exists()
        )

    def test_create_without_password_fails(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse("accounts:users-list"), {"username": "doc2", "role": "DOCTOR"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_cannot_deactivate_self(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            reverse("accounts:users-detail", args=[self.admin.pk]), {"is_active": False}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_admin_resets_password(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse("accounts:users-reset-password", args=[self.nurse.pk]),
            {"new_password": "N3w-nurse-pass-456"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.nurse.refresh_from_db()
        self.assertTrue(self.nurse.check_password("N3w-nurse-pass-456"))

    def test_change_own_password_requires_correct_old_password(self):
        self.client.force_authenticate(self.nurse)
        url = reverse("accounts:change-password")
        wrong = self.client.post(
            url, {"old_password": "wrong", "new_password": "N3w-nurse-pass-456"}, format="json"
        )
        self.assertEqual(wrong.status_code, status.HTTP_400_BAD_REQUEST)
        right = self.client.post(
            url, {"old_password": "Nurs3-pass-123", "new_password": "N3w-nurse-pass-456"}, format="json"
        )
        self.assertEqual(right.status_code, status.HTTP_204_NO_CONTENT)
