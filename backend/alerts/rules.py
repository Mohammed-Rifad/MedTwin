from dataclasses import dataclass

from equipment.models import Equipment

from .models import Alert


@dataclass(frozen=True)
class Rule:
    kind: str
    label: str
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


# Vital signs: limits based on NEWS2 (Royal College of Physicians, 2017). Keys are VitalReading fields.
VITAL_RULES = {
    "spo2": Rule(Alert.Kind.LOW_SPO2, "SpO₂", "%", "below", warning=91, critical=87, clear=94),
    "heart_rate": Rule(Alert.Kind.HIGH_HEART_RATE, "Heart rate", "/min", "above", warning=120, critical=140, clear=110),
    "systolic_bp": Rule(Alert.Kind.LOW_BLOOD_PRESSURE, "Systolic BP", " mmHg", "below", warning=90, critical=80, clear=95),
    "respiratory_rate": Rule(Alert.Kind.HIGH_RESPIRATORY_RATE, "Respiratory rate", "/min", "above", warning=25, critical=30, clear=21),
    "temperature": Rule(Alert.Kind.FEVER, "Temperature", " °C", "above", warning=38.5, critical=39.5, clear=38.0),
}

OCCUPANCY_RULE = Rule(Alert.Kind.HIGH_OCCUPANCY, "Occupancy", "%", "above", warning=85, critical=100, clear=75)

# Machine temperature: a few degrees above each kind's normal working temperature.
EQUIPMENT_TEMPERATURE_RULES = {
    Equipment.Kind.VENTILATOR: Rule(Alert.Kind.EQUIPMENT_OVERHEATING, "Temperature", " °C", "above", warning=44, critical=47, clear=42),
    Equipment.Kind.MONITOR: Rule(Alert.Kind.EQUIPMENT_OVERHEATING, "Temperature", " °C", "above", warning=40, critical=43, clear=38),
    Equipment.Kind.INFUSION_PUMP: Rule(Alert.Kind.EQUIPMENT_OVERHEATING, "Temperature", " °C", "above", warning=37, critical=40, clear=35),
}
