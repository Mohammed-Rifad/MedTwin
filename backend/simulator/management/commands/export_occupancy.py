import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max, Min

from hospital.models import Admission
from simulator.occupancy import capacities, hourly_occupancy
from twin import clock


class Command(BaseCommand):
    help = "Export hourly occupancy per unit type (from the history) as a CSV file for the ICU forecast notebook."

    def add_arguments(self, parser):
        default = Path(__file__).resolve().parents[4] / "ml" / "data" / "occupancy_hourly.csv"
        parser.add_argument("--out", default=str(default), help="Where to write the CSV file.")

    def handle(self, *args, **options):
        span = Admission.objects.aggregate(first=Min("admitted_at"), last=Max("admitted_at"))
        if span["first"] is None:
            raise CommandError("No admissions yet. Run generate_history first.")
        start = span["first"].replace(minute=0, second=0, microsecond=0)
        end = clock.now().replace(minute=0, second=0, microsecond=0)

        out = Path(options["out"])
        out.parent.mkdir(parents=True, exist_ok=True)
        rows = 0
        with out.open("w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["time", "ICU", "WARD", "ED", "icu_admissions", "ed_arrivals"])
            writer.writeheader()
            for row in hourly_occupancy(start, end):
                writer.writerow({**row, "time": row["time"].isoformat()})
                rows += 1

        # The bed counts go alongside, so the notebook knows each unit's capacity.
        out.with_suffix(".json").write_text(json.dumps({"capacity": capacities(), "start": start.isoformat(), "end": end.isoformat()}, indent=2))
        self.stdout.write(self.style.SUCCESS(f"Wrote {rows} hours ({rows / 24:.0f} days) to {out}"))
