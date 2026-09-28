from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        DOCTOR = "DOCTOR", "Doctor"
        NURSE = "NURSE", "Nurse"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.NURSE)

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_clinical(self):
        return self.role in (self.Role.DOCTOR, self.Role.NURSE)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
