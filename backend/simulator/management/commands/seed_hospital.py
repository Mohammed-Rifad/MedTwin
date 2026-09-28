from collections import Counter

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import User
from equipment.models import Equipment
from hospital.models import Admission, Bed, EmergencyArrival, Patient, Unit

# code, name, type, (x, y, width, height) on the 1000x600 map, rows, columns
UNITS = [
    ("ICU", "Intensive Care Unit", Unit.UnitType.ICU, (20, 20, 460, 270), 2, 6),
    ("ED", "Emergency Department", Unit.UnitType.ED, (520, 20, 460, 270), 2, 5),
    ("WA", "Ward A", Unit.UnitType.WARD, (20, 310, 460, 270), 3, 5),
    ("WB", "Ward B", Unit.UnitType.WARD, (520, 310, 460, 270), 3, 5),
]

# kind, code prefix, model name, unit code, how many (attached to that unit's first beds)
EQUIPMENT = [
    (Equipment.Kind.VENTILATOR, "VENT", "Hamilton C6", "ICU", 8),
    (Equipment.Kind.MONITOR, "MON", "Philips IntelliVue MX800", "ICU", 12),
    (Equipment.Kind.MONITOR, "MON", "Philips IntelliVue MX450", "ED", 4),
    (Equipment.Kind.INFUSION_PUMP, "PUMP", "BD Alaris 8015", "ICU", 4),
    (Equipment.Kind.INFUSION_PUMP, "PUMP", "BD Alaris 8015", "WA", 1),
    (Equipment.Kind.INFUSION_PUMP, "PUMP", "BD Alaris 8015", "WB", 1),
]

DEMO_USERS = [
    ("demo_admin", User.Role.ADMIN),
    ("demo_doctor", User.Role.DOCTOR),
    ("demo_nurse", User.Role.NURSE),
]


def bed_positions(x, y, width, height, rows, cols, padding=20, header=40):
    """Yield the centre point of each bed, laid out in a grid inside the unit's rectangle."""
    cell_width = (width - 2 * padding) / cols
    cell_height = (height - header - padding) / rows
    for row in range(rows):
        for col in range(cols):
            yield (
                round(x + padding + cell_width * (col + 0.5)),
                round(y + header + cell_height * (row + 0.5)),
            )


class Command(BaseCommand):
    help = "Create the demo hospital: units, beds, equipment and demo users."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete all hospital data first.")
        parser.add_argument("--password", default="medtwin-demo", help="Password for new demo users.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self.reset()
        elif Unit.objects.exists():
            raise CommandError("Hospital data already exists. Use --reset to rebuild it.")

        units = self.create_units_and_beds()
        devices = self.create_equipment(units)
        users = self.create_demo_users(options["password"])

        self.stdout.write(self.style.SUCCESS(
            f"Created {len(units)} units, {Bed.objects.count()} beds and {devices} devices."
        ))
        if users:
            self.stdout.write(f"New demo users (password '{options['password']}'): {', '.join(users)}")

    def reset(self):
        EmergencyArrival.objects.all().delete()
        Admission.objects.all().delete()
        Patient.objects.all().delete()
        Equipment.objects.all().delete()
        Bed.objects.all().delete()
        Unit.objects.all().delete()
        self.stdout.write("Deleted existing hospital data.")

    def create_units_and_beds(self):
        units = {}
        for code, name, unit_type, (x, y, width, height), rows, cols in UNITS:
            unit = Unit.objects.create(
                code=code, name=name, unit_type=unit_type,
                map_x=x, map_y=y, map_width=width, map_height=height,
            )
            Bed.objects.bulk_create(
                Bed(unit=unit, code=f"{code}-{number:02d}", map_x=bx, map_y=by)
                for number, (bx, by) in enumerate(bed_positions(x, y, width, height, rows, cols), start=1)
            )
            units[code] = unit
        return units

    def create_equipment(self, units):
        numbers = Counter()
        devices = []
        for kind, prefix, model_name, unit_code, count in EQUIPMENT:
            unit = units[unit_code]
            for bed in unit.beds.order_by("code")[:count]:
                numbers[prefix] += 1
                devices.append(Equipment(
                    code=f"{prefix}-{numbers[prefix]:02d}", kind=kind,
                    model_name=model_name, unit=unit, bed=bed,
                ))
        Equipment.objects.bulk_create(devices)
        return len(devices)

    def create_demo_users(self, password):
        created = []
        for username, role in DEMO_USERS:
            user, is_new = User.objects.get_or_create(
                username=username,
                defaults={"role": role, "is_staff": role == User.Role.ADMIN},
            )
            if is_new:
                user.set_password(password)
                user.save(update_fields=["password"])
                created.append(username)
        return created
