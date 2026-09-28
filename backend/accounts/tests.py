from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


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
