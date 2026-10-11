from django.db import IntegrityError, transaction

from config.errors import DomainError
from twin import clock, events

from . import rules
from .models import Alert, AlertThreshold

SEVERITY_RANK = {Alert.Severity.INFO: 0, Alert.Severity.WARNING: 1, Alert.Severity.CRITICAL: 2}


class AlertError(DomainError):
    """Raised when an alert action isn't allowed, e.g. acknowledging a resolved alert."""


def active_alerts():
    return Alert.objects.exclude(status=Alert.Status.RESOLVED)


def raise_alert(*, kind, subject, severity, message, value=None, at=None, **related):
    """Create an alert, or update the active one for the same problem. Never creates duplicates."""
    at = at or clock.now()
    alert = active_alerts().filter(kind=kind, subject=subject).first()
    if alert is None:
        try:
            with transaction.atomic():
                alert = Alert.objects.create(
                    kind=kind, subject=subject, severity=severity, message=message,
                    value=value, created_at=at, last_seen_at=at, **related,
                )
            events.alert_changed(alert)
            return alert
        except IntegrityError:
            # Another process created it a moment ago: update that one instead.
            alert = active_alerts().get(kind=kind, subject=subject)

    alert.value = value
    alert.last_seen_at = at
    fields = ["value", "last_seen_at"]
    got_worse = SEVERITY_RANK[severity] > SEVERITY_RANK[alert.severity]
    if got_worse:
        alert.severity = severity
        alert.message = message
        fields += ["severity", "message"]
    alert.save(update_fields=fields)
    if got_worse:
        events.alert_changed(alert)  # only announce real changes, not every repeat reading
    return alert


def resolve_alerts(*, subject, kind=None, at=None, by=None):
    """Close the active alerts for a subject (optionally only one kind). Returns how many were closed."""
    alerts = active_alerts().filter(subject=subject)
    if kind is not None:
        alerts = alerts.filter(kind=kind)
    closed = 0
    for alert in alerts:
        _close(alert, at=at or clock.now(), by=by)
        closed += 1
    return closed


def acknowledge_alert(*, alert, by, at=None):
    """A member of staff says "I'm on it"."""
    if alert.status != Alert.Status.OPEN:
        raise AlertError("Only open alerts can be acknowledged.")
    alert.status = Alert.Status.ACKNOWLEDGED
    alert.acknowledged_at = at or clock.now()
    alert.acknowledged_by = by
    alert.save(update_fields=["status", "acknowledged_at", "acknowledged_by"])
    events.alert_changed(alert)
    return alert


def resolve_alert(*, alert, by, at=None):
    """A member of staff says the problem has been dealt with."""
    if alert.status == Alert.Status.RESOLVED:
        raise AlertError("This alert is already resolved.")
    _close(alert, at=at or clock.now(), by=by)
    return alert


def _close(alert, *, at, by):
    alert.status = Alert.Status.RESOLVED
    alert.resolved_at = at
    alert.resolved_by = by
    alert.save(update_fields=["status", "resolved_at", "resolved_by"])
    events.alert_changed(alert)


def set_threshold(*, key, warning, critical, clear, by=None):
    """Change one rule's limits. Takes effect within a few seconds everywhere."""
    if key not in rules.DEFAULT_RULES:
        raise AlertError(f"Unknown rule: {key}.")
    rule = rules.DEFAULT_RULES[key]
    if not rule.limits_in_order(warning, critical, clear):
        if rule.direction == "above":
            raise AlertError("For this rule, the limits must be: clear < warning ≤ critical.")
        raise AlertError("For this rule, the limits must be: clear > warning ≥ critical.")
    AlertThreshold.objects.update_or_create(
        key=key, defaults={"warning": warning, "critical": critical, "clear": clear, "updated_by": by}
    )
    rules.clear_cache()
    return rules.get_rule(key)


def reset_threshold(*, key):
    """Go back to the default limits for one rule."""
    if key not in rules.DEFAULT_RULES:
        raise AlertError(f"Unknown rule: {key}.")
    AlertThreshold.objects.filter(key=key).delete()
    rules.clear_cache()
    return rules.get_rule(key)
