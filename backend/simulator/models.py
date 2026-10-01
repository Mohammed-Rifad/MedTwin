from datetime import timedelta

from django.db import models

from equipment.models import Equipment
from hospital.models import Admission


class PatientPhysiology(models.Model):
    """The simulator's hidden state for one admission. Staff never see this, only the vital signs it produces."""

    admission = models.OneToOneField(Admission, on_delete=models.CASCADE, related_name="physiology")
    baseline = models.JSONField()
    deterioration_onset_at = models.DateTimeField(null=True, blank=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    last_reading_at = models.DateTimeField(null=True, blank=True)
    last_temperature_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "patient physiology"

    def __str__(self):
        return f"Physiology for admission {self.admission_id}"

    @property
    def deteriorates(self):
        return self.deterioration_onset_at is not None


class InjectedFault(models.Model):
    """A fault the simulator put into a device: ground truth for evaluating anomaly detection."""

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name="injected_faults")
    started_at = models.DateTimeField()
    hours_to_failure = models.FloatField()
    failed_at = models.DateTimeField(null=True, blank=True)
    cleared_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Fault in {self.equipment.code} from {self.started_at:%Y-%m-%d %H:%M}"

    def progress(self, at):
        """0 at the start of the fault, 1 when the device fails."""
        if at < self.started_at:
            return 0.0
        return min(1.0, (at - self.started_at) / timedelta(hours=self.hours_to_failure))

    @property
    def caught_before_failure(self):
        return self.cleared_at is not None and self.failed_at is None
