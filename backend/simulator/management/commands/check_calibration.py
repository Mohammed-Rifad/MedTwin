from django.core.management.base import BaseCommand

from hospital.models import Bed
from simulator.calibration import expected_census


class Command(BaseCommand):
    help = "Show how full each unit should be with the current simulator settings."

    def handle(self, *args, **options):
        for unit_type, patients in expected_census().items():
            beds = Bed.objects.filter(unit__unit_type=unit_type, is_active=True).count()
            occupancy = f"{100 * patients / beds:4.0f}%" if beds else "  n/a"
            self.stdout.write(f"{unit_type:<5} expected {patients:5.1f} patients in {beds:3d} beds  {occupancy}")
