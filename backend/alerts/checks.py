from .models import Alert
from .rules import EQUIPMENT_TEMPERATURE_RULES, OCCUPANCY_RULE, VITAL_RULES
from .services import active_alerts, raise_alert, resolve_alerts


def _open_kinds(subject):
    return set(active_alerts().filter(subject=subject).values_list("kind", flat=True))


def _apply(rule, value, subject, open_kinds, at, name, **related):
    """Raise or update an alert if the value breaks the rule; close it once the value has cleared."""
    severity = rule.severity_for(value)
    if severity:
        raise_alert(
            kind=rule.kind, subject=subject, severity=severity,
            message=f"{name()}: {rule.describe(value)}", value=value, at=at, **related,
        )
    elif rule.kind in open_kinds and rule.has_cleared(value):
        resolve_alerts(subject=subject, kind=rule.kind, at=at)


def check_vitals(reading):
    admission = reading.admission
    subject = f"admission:{admission.pk}"
    open_kinds = _open_kinds(subject)
    name = lambda: f"{admission.patient.full_name} ({admission.bed.code})"  # noqa: E731
    for field, rule in VITAL_RULES.items():
        value = getattr(reading, field)
        if value is not None:
            _apply(rule, value, subject, open_kinds, reading.recorded_at, name, admission=admission)


def check_occupancy(unit, at):
    if unit.capacity == 0:
        return
    occupancy = round(100 * unit.occupied_count / unit.capacity)
    subject = f"unit:{unit.pk}"
    _apply(OCCUPANCY_RULE, occupancy, subject, _open_kinds(subject), at, lambda: unit.name, unit=unit)


def check_telemetry(reading):
    equipment = reading.equipment
    rule = EQUIPMENT_TEMPERATURE_RULES[equipment.kind]
    subject = f"equipment:{equipment.pk}"
    _apply(rule, reading.temperature, subject, _open_kinds(subject), reading.recorded_at, lambda: equipment.code, equipment=equipment)


def equipment_failed(equipment, at):
    raise_alert(
        kind=Alert.Kind.EQUIPMENT_FAILURE, subject=f"equipment:{equipment.pk}",
        severity=Alert.Severity.CRITICAL, message=f"{equipment.code} has failed",
        at=at, equipment=equipment,
    )


def equipment_repaired(equipment, at):
    resolve_alerts(subject=f"equipment:{equipment.pk}", at=at)


def patient_left(admission, at):
    resolve_alerts(subject=f"admission:{admission.pk}", at=at)
