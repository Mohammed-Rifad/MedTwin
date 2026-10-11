import csv
import gzip
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from equipment.models import EquipmentReading
from simulator.models import InjectedFault


class Command(BaseCommand):
    help = "Export equipment telemetry and the simulator's injected faults (the ground truth) for the anomaly notebook."

    def add_arguments(self, parser):
        default = Path(__file__).resolve().parents[4] / "ml" / "data"
        parser.add_argument("--out-dir", default=str(default), help="Folder for telemetry.csv.gz and faults.csv.")

    def handle(self, *args, **options):
        if not EquipmentReading.objects.exists():
            raise CommandError("No equipment readings yet. Run generate_history first.")
        out = Path(options["out_dir"])
        out.mkdir(parents=True, exist_ok=True)

        readings = EquipmentReading.objects.select_related("equipment").order_by("equipment_id", "recorded_at")
        count = 0
        with gzip.open(out / "telemetry.csv.gz", "wt", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["equipment", "code", "kind", "recorded_at", "temperature", "running_hours", "error_count", "pressure"])
            for reading in readings.iterator(chunk_size=5000):
                writer.writerow([
                    reading.equipment_id, reading.equipment.code, reading.equipment.kind, reading.recorded_at.isoformat(),
                    reading.temperature, reading.running_hours, reading.error_count,
                    "" if reading.pressure is None else reading.pressure,
                ])
                count += 1

        faults = InjectedFault.objects.select_related("equipment").order_by("started_at")
        with (out / "faults.csv").open("w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["equipment", "code", "kind", "started_at", "hours_to_failure", "failed_at", "cleared_at"])
            for fault in faults:
                writer.writerow([
                    fault.equipment_id, fault.equipment.code, fault.equipment.kind, fault.started_at.isoformat(),
                    fault.hours_to_failure, fault.failed_at.isoformat() if fault.failed_at else "",
                    fault.cleared_at.isoformat() if fault.cleared_at else "",
                ])

        self.stdout.write(self.style.SUCCESS(f"Wrote {count:,} readings and {faults.count()} faults to {out}"))
