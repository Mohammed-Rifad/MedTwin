from django.db import models
from django.utils import timezone


class HospitalClock(models.Model):
    """The digital twin's own clock. It can run faster than real time, or be paused."""

    speed = models.FloatField(default=60)
    running = models.BooleanField(default=False)
    anchor_sim_time = models.DateTimeField(null=True, blank=True)
    anchor_real_time = models.DateTimeField(null=True, blank=True)
    heartbeat_at = models.DateTimeField(null=True, blank=True)

    CLOCK_FIELDS = ["speed", "running", "anchor_sim_time", "anchor_real_time"]

    def __str__(self):
        state = "running" if self.running else "paused"
        return f"Hospital clock ({state}, {self.speed:g}x)"

    @classmethod
    def load(cls):
        clock, _ = cls.objects.get_or_create(pk=1)
        return clock

    def now(self):
        if self.anchor_sim_time is None:
            return timezone.now()
        if not self.running:
            return self.anchor_sim_time
        return self.anchor_sim_time + (timezone.now() - self.anchor_real_time) * self.speed

    def start(self, speed=None):
        self._re_anchor()
        if speed is not None:
            self.speed = speed
        self.running = True
        self.save(update_fields=self.CLOCK_FIELDS)


    def pause(self):
        self._re_anchor()
        self.running = False
        self.save(update_fields=self.CLOCK_FIELDS)


    def _re_anchor(self):
        self.anchor_sim_time = self.now()
        self.anchor_real_time = timezone.now()
