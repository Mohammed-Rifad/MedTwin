from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from equipment.models import Equipment
from hospital.models import Admission, Unit


class Alert(models.Model):
    class Kind(models.TextChoices):
        LOW_SPO2 = "LOW_SPO2", "Low oxygen saturation"
        HIGH_HEART_RATE = "HIGH_HEART_RATE", "High heart rate"
        LOW_BLOOD_PRESSURE = "LOW_BLOOD_PRESSURE", "Low blood pressure"
        HIGH_RESPIRATORY_RATE = "HIGH_RESPIRATORY_RATE", "High respiratory rate"
        FEVER = "FEVER", "Fever"
        HIGH_OCCUPANCY = "HIGH_OCCUPANCY", "High bed occupancy"
        EQUIPMENT_OVERHEATING = "EQUIPMENT_OVERHEATING", "Equipment overheating"
        EQUIPMENT_FAILURE = "EQUIPMENT_FAILURE", "Equipment failure"

    class Severity(models.TextChoices):
        INFO = "INFO", "Info"
        WARNING = "WARNING", "Warning"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"
        RESOLVED = "RESOLVED", "Resolved"

    kind = models.CharField(max_length=30, choices=Kind.choices)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    subject = models.CharField(max_length=50, help_text='What the alert is about, e.g. "admission:12".')
    message = models.CharField(max_length=255)
    value = models.FloatField(null=True, blank=True)

    admission = models.ForeignKey(Admission, null=True, blank=True, on_delete=models.CASCADE, related_name="alerts")
    equipment = models.ForeignKey(Equipment, null=True, blank=True, on_delete=models.CASCADE, related_name="alerts")
    unit = models.ForeignKey(Unit, null=True, blank=True, on_delete=models.CASCADE, related_name="alerts")

    created_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"])]
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "subject"],
                condition=~Q(status="RESOLVED"),
                name="one_active_alert_per_problem",
            ),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.message}"
