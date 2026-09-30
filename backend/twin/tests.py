from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

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
