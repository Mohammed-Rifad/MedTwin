import time
from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from hospital.models import Admission, VitalReading
from simulator.engine import Simulator
from twin.models import HospitalClock


class Command(BaseCommand):
    help = "Rebuild the hospital and simulate its recent past, ending now."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=180)
        parser.add_argument("--step-minutes", type=int, default=30)
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--reset", action="store_true", help="Required: confirms deleting all hospital data.")

    def handle(self, *args, **options):
        if not options["reset"]:
            raise CommandError("This deletes all hospital data. Run again with --reset to confirm.")
        call_command("seed_hospital", "--reset", stdout=self.stdout)

        end = timezone.now().replace(second=0, microsecond=0)
        start = end - timedelta(days=options["days"])
        step = timedelta(minutes=options["step_minutes"])
        simulator = Simulator(seed=options["seed"], history=True)
        started = time.monotonic()

        now = start
        while now < end:
            now = min(now + step, end)
            simulator.step(now, step / timedelta(hours=1))
            simulator.flush()
            if (now - start) % timedelta(days=7) < step:
                self.stdout.write(
                    f"{timezone.localtime(now):%d %b %Y}: {Admission.objects.count()} admissions, "
                    f"{VitalReading.objects.count()} vital readings ({time.monotonic() - started:.0f}s)"
                )

        clock = HospitalClock.load()
        clock.anchor_sim_time = end
        clock.anchor_real_time = timezone.now()
        clock.running = False
        clock.save()
        self.stdout.write(self.style.SUCCESS(
            f"Simulated {options['days']} days in {time.monotonic() - started:.0f}s. "
            "Start the live simulator with run_simulator."
        ))
