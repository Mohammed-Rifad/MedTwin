from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from alerts.models import Alert
from equipment.models import Equipment
from hospital.models import Admission, Bed, EmergencyArrival, Unit

from . import clock


def _counts(queryset, field):
    """{value: how many}, e.g. {"OK": 27, "FAULT": 1} for equipment status."""
    return dict(queryset.order_by().values_list(field).annotate(total=Count("id")))


@api_view(["GET"])
def summary(request):
    """Everything the dashboard shows, in one request (instead of five)."""
    now = clock.now()
    start_of_day = timezone.localtime(now).replace(hour=0, minute=0, second=0, microsecond=0)

    active = Q(beds__is_active=True)
    units = Unit.objects.annotate(
        _capacity=Count("beds", filter=active),
        _occupied=Count("beds", filter=active & Q(beds__status=Bed.Status.OCCUPIED)),
        _cleaning=Count("beds", filter=active & Q(beds__status=Bed.Status.CLEANING)),
    ).order_by("floor", "name")
    unit_rows = [
        {
            "code": unit.code,
            "name": unit.name,
            "unit_type": unit.unit_type,
            "capacity": unit._capacity,
            "occupied": unit._occupied,
            "cleaning": unit._cleaning,
        }
        for unit in units
    ]
    icu = [row for row in unit_rows if row["unit_type"] == Unit.UnitType.ICU]
    icu_capacity = sum(row["capacity"] for row in icu)
    icu_occupied = sum(row["occupied"] for row in icu)

    beds = Bed.objects.aggregate(
        total=Count("id", filter=Q(is_active=True)),
        occupied=Count("id", filter=Q(is_active=True, status=Bed.Status.OCCUPIED)),
        cleaning=Count("id", filter=Q(is_active=True, status=Bed.Status.CLEANING)),
        free=Count("id", filter=Q(is_active=True, status=Bed.Status.FREE)),
        closed=Count("id", filter=Q(is_active=False)),
    )

    waiting = EmergencyArrival.objects.filter(status=EmergencyArrival.Status.WAITING)
    active_alerts = Alert.objects.exclude(status=Alert.Status.RESOLVED)

    return Response({
        "hospital_time": now,
        "units": unit_rows,
        "beds": beds,
        "icu": {
            "occupied": icu_occupied,
            "capacity": icu_capacity,
            "percent": round(100 * icu_occupied / icu_capacity) if icu_capacity else 0,
        },
        "emergency": {"waiting": waiting.count(), "by_triage": _counts(waiting, "triage_level")},
        "alerts": {
            "open": active_alerts.filter(status=Alert.Status.OPEN).count(),
            "acknowledged": active_alerts.filter(status=Alert.Status.ACKNOWLEDGED).count(),
            "by_severity": _counts(active_alerts, "severity"),
            "by_kind": _counts(active_alerts, "kind"),
        },
        "equipment": {"total": Equipment.objects.count(), "by_status": _counts(Equipment.objects, "status")},
        "today": {
            "admissions": Admission.objects.filter(admitted_at__gte=start_of_day, admitted_at__lte=now).count(),
            "discharges": Admission.objects.filter(discharged_at__gte=start_of_day, discharged_at__lte=now).count(),
        },
    })
