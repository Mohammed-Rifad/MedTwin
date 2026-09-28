from django.core.management import CommandError, call_command
from django.test import TestCase

from accounts.models import User
from equipment.models import Equipment
from hospital.models import Bed, Unit


class SeedHospitalTests(TestCase):
    def seed(self, *args):
        call_command("seed_hospital", *args, stdout=open("nul", "w"))

    def test_creates_demo_hospital(self):
        self.seed()
        self.assertEqual(Unit.objects.count(), 4)
        self.assertEqual(Bed.objects.count(), 52)
        self.assertFalse(Bed.objects.exclude(status=Bed.Status.FREE).exists())
        self.assertEqual(Equipment.objects.count(), 30)
        self.assertEqual(User.objects.get(username="demo_doctor").role, User.Role.DOCTOR)

    def test_refuses_to_seed_twice_without_reset(self):
        self.seed()
        with self.assertRaises(CommandError):
            self.seed()

    def test_reset_rebuilds_the_same_hospital(self):
        self.seed()
        self.seed("--reset")
        self.assertEqual(Bed.objects.count(), 52)
        self.assertEqual(Equipment.objects.count(), 30)

    def test_beds_are_inside_their_unit_on_the_map(self):
        self.seed()
        for bed in Bed.objects.select_related("unit"):
            unit = bed.unit
            self.assertTrue(unit.map_x < bed.map_x < unit.map_x + unit.map_width, bed.code)
            self.assertTrue(unit.map_y < bed.map_y < unit.map_y + unit.map_height, bed.code)
