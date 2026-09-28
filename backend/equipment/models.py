from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from hospital.models import Bed, Unit


class Equipment(models.Model):
    class Kind(models.TextChoices):
        VENTILATOR = "VENTILATOR", "Ventilator"
        MONITOR = "MONITOR", "Patient monitor"
        INFUSION_PUMP = "INFUSION_PUMP", "Infusion pump"

    class Status(models.TextChoices):
        OK = "OK", "OK"
        WARNING = "WARNING", "Warning"
        FAULT = "FAULT", "Fault"
        MAINTENANCE = "MAINTENANCE", "In maintenance"

    code = models.CharField(max_length=20, unique=True)
    kind = models.CharField(max_length=15, choices=Kind.choices)
    model_name = models.CharField(max_length=100, blank=True)
    unit = models.ForeignKey(Unit, null=True, blank=True, on_delete=models.SET_NULL, related_name="equipment")
    bed = models.ForeignKey(Bed, null=True, blank=True, on_delete=models.SET_NULL, related_name="equipment")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OK)
    installed_on = models.DateField(null=True, blank=True)
    last_serviced_at = models.DateTimeField(null=True, blank=True)
    anomaly_score = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["code"]
        verbose_name_plural = "equipment"

    def __str__(self):
        return f"{self.code} ({self.get_kind_display()})"


class EquipmentReading(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name="readings")
    recorded_at = models.DateTimeField(default=timezone.now)
    temperature = models.FloatField("Internal temperature (°C)")
    running_hours = models.FloatField()
    error_count = models.PositiveIntegerField(default=0)
    pressure = models.FloatField("Pressure (cmH₂O)", null=True, blank=True)

    class Meta:
        ordering = ["-recorded_at"]
        indexes = [models.Index(fields=["equipment", "-recorded_at"])]

    def __str__(self):
        return f"{self.equipment.code} at {self.recorded_at:%Y-%m-%d %H:%M}"


class MaintenanceLog(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name="maintenance_logs")
    reason = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    finished_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["equipment"],
                condition=Q(finished_at__isnull=True),
                name="one_open_maintenance_per_equipment",
            ),
        ]

    def __str__(self):
        return f"{self.equipment.code}: {self.reason}"

    @property
    def is_open(self):
        return self.finished_at is None
