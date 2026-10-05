from django.db import IntegrityError, transaction
from twin import clock
from .models import Alert

SEVERITY_RANK = {Alert.Severity.INFO: 0, Alert.Severity.WARNING: 1, Alert.Severity.CRITICAL: 2}


def active_alerts():
    return Alert.objects.exclude(status=Alert.Status.RESOLVED)


def raise_alert(*, kind, subject, severity, message, value=None, at=None, **related):
    """Create an alert, or update the active one for the same problem. Never creates duplicates."""
    at = at or clock.now()
    alert = active_alerts().filter(kind=kind, subject=subject).first()
    if alert is None:
        try:
            with transaction.atomic():
                return Alert.objects.create(
                    kind=kind, subject=subject, severity=severity, message=message,
                    value=value, created_at=at, last_seen_at=at, **related,
                )
        except IntegrityError:
            # Another process created it a moment ago: update that one instead.
            alert = active_alerts().get(kind=kind, subject=subject)

    alert.value = value
    alert.last_seen_at = at
    fields = ["value", "last_seen_at"]
    if SEVERITY_RANK[severity] > SEVERITY_RANK[alert.severity]:
        alert.severity = severity
        alert.message = message
        fields += ["severity", "message"]
    alert.save(update_fields=fields)
    return alert


def resolve_alerts(*, subject, kind=None, at=None, by=None):
    """Close the active alerts for a subject (optionally only one kind). Returns how many were closed."""
    alerts = active_alerts().filter(subject=subject)
    if kind is not None:
        alerts = alerts.filter(kind=kind)
    return alerts.update(status=Alert.Status.RESOLVED, resolved_at=at or clock.now(), resolved_by=by)
