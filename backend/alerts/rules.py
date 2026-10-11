import time
from dataclasses import dataclass, replace

from django.conf import settings

from equipment.models import Equipment

from .models import Alert, AlertThreshold


@dataclass(frozen=True)
class Rule:
    kind: str
    name: str  # shown on the thresholds screen, e.g. "Ventilator temperature"
    label: str  # shown in alert messages, e.g. "Temperature"
    unit: str
    direction: str  # "above" or "below": which side is dangerous
    warning: float
    critical: float
    clear: float

    def _reached(self, value, limit):
        return value >= limit if self.direction == "above" else value <= limit

    def severity_for(self, value):
        """CRITICAL, WARNING, or None if the value is fine."""
        if self._reached(value, self.critical):
            return Alert.Severity.CRITICAL
        if self._reached(value, self.warning):
            return Alert.Severity.WARNING
        return None

    def has_cleared(self, value):
        """True once the value is safely back on the good side of the clear line."""
        return value < self.clear if self.direction == "above" else value > self.clear

    def describe(self, value):
        limit = self.critical if self._reached(value, self.critical) else self.warning
        sign = "≥" if self.direction == "above" else "≤"
        return f"{self.label} {value:g}{self.unit} ({sign} {limit:g}{self.unit})"

    def limits_in_order(self, warning, critical, clear):
        """True if the three limits make sense together, e.g. for "below": clear > warning >= critical."""
        if self.direction == "above":
            return clear < warning <= critical
        return clear > warning >= critical


def equipment_temperature_key(kind):
    return f"equipment_temperature:{kind}"


# Vital-sign fields that have a rule. The rule key is the VitalReading field name.
VITAL_FIELDS = ("spo2", "heart_rate", "systolic_bp", "respiratory_rate", "temperature")

# Default limits. Admins can override any of them (stored in AlertThreshold).
# Vital signs: based on NEWS2 (Royal College of Physicians, 2017).
# Machines: a few degrees above each kind's normal working temperature.
DEFAULT_RULES = {
    "spo2": Rule(Alert.Kind.LOW_SPO2, "Low oxygen saturation", "SpO₂", "%", "below", 91, 87, 94),
    "heart_rate": Rule(Alert.Kind.HIGH_HEART_RATE, "High heart rate", "Heart rate", "/min", "above", 120, 140, 110),
    "systolic_bp": Rule(Alert.Kind.LOW_BLOOD_PRESSURE, "Low blood pressure", "Systolic BP", " mmHg", "below", 90, 80, 95),
    "respiratory_rate": Rule(Alert.Kind.HIGH_RESPIRATORY_RATE, "High breathing rate", "Respiratory rate", "/min", "above", 25, 30, 21),
    "temperature": Rule(Alert.Kind.FEVER, "Fever", "Temperature", " °C", "above", 38.5, 39.5, 38.0),
    "occupancy": Rule(Alert.Kind.HIGH_OCCUPANCY, "Unit occupancy", "Occupancy", "%", "above", 85, 100, 75),
    equipment_temperature_key(Equipment.Kind.VENTILATOR): Rule(
        Alert.Kind.EQUIPMENT_OVERHEATING, "Ventilator temperature", "Temperature", " °C", "above", 44, 47, 42
    ),
    equipment_temperature_key(Equipment.Kind.MONITOR): Rule(
        Alert.Kind.EQUIPMENT_OVERHEATING, "Monitor temperature", "Temperature", " °C", "above", 40, 43, 38
    ),
    equipment_temperature_key(Equipment.Kind.INFUSION_PUMP): Rule(
        Alert.Kind.EQUIPMENT_OVERHEATING, "Infusion pump temperature", "Temperature", " °C", "above", 37, 40, 35
    ),
}

# Overrides are read from the database at most every few seconds, not on every reading.
_cache = {"loaded_at": None, "overrides": {}}


def overrides():
    """Admin changes, by rule key. Cached for ALERT_THRESHOLD_CACHE_SECONDS."""
    now = time.monotonic()
    if _cache["loaded_at"] is None or now - _cache["loaded_at"] >= settings.ALERT_THRESHOLD_CACHE_SECONDS:
        _cache["overrides"] = {row.key: row for row in AlertThreshold.objects.select_related("updated_by")}
        _cache["loaded_at"] = now
    return _cache["overrides"]


def clear_cache():
    _cache["loaded_at"] = None


def get_rule(key):
    """The rule for a key, with the admin's limits if they changed them."""
    rule = DEFAULT_RULES[key]
    override = overrides().get(key)
    if override is None:
        return rule
    return replace(rule, warning=override.warning, critical=override.critical, clear=override.clear)
