import time

from django.core.management.base import BaseCommand
from django.utils import timezone
from twin import events
from config.errors import DomainError
from hospital.models import EmergencyArrival, Unit
from simulator.engine import Simulator
from twin.models import HospitalClock


class Command(BaseCommand):
    help = "Run the live hospital simulator. Press Ctrl+C to stop."

    def add_arguments(self, parser):
        parser.add_argument("--speed", type=float, default=60, help="Hospital seconds per real second.")
        parser.add_argument("--tick", type=float, default=1.0, help="Real seconds between steps.")
        parser.add_argument("--seed", type=int, default=None, help="Random seed for a repeatable run.")

    def handle(self, *args, **options):
        simulator = Simulator(seed=options["seed"])
        clock = HospitalClock.load()
        clock.start(speed=options["speed"])
        last = clock.now()
        last_report = None
        self.stdout.write(
            f"Simulator running at {clock.speed:g}x (seed {simulator.seed}), "
            f"hospital time {timezone.localtime(last):%Y-%m-%d %H:%M}. Press Ctrl+C to stop."
        )

        try:
            while True:
                time.sleep(options["tick"])
                HospitalClock.objects.filter(pk=1).update(heartbeat_at=timezone.now())

                clock.refresh_from_db()
                events.clock_ticked(clock)

                now = clock.now()
                if now <= last:
                    continue  # paused
                try:
                    simulator.step(now, (now - last).total_seconds() / 3600)
                except DomainError as error:
                    self.stderr.write(f"Skipped an event: {error}")
                last = now
                hour = timezone.localtime(now).replace(minute=0, second=0, microsecond=0)
                if hour != last_report:
                    last_report = hour
                    self.report(now)
        except KeyboardInterrupt:
            clock.refresh_from_db()
            clock.pause()
            self.stdout.write("\nSimulator stopped. Hospital clock paused.")

    def report(self, now):
        units = "  ".join(f"{unit.code} {unit.occupied_count}/{unit.capacity}" for unit in Unit.objects.order_by("code"))
        waiting = EmergencyArrival.objects.filter(status=EmergencyArrival.Status.WAITING).count()
        self.stdout.write(f"{timezone.localtime(now):%a %d %b %H:%M}  {units}  ED queue {waiting}")
