from dataclasses import dataclass, field

# Relative ED arrival rate for each hour of the day (0 = midnight). Average is about 1.
HOURLY_PATTERN = (
    0.5, 0.4, 0.35, 0.3, 0.3, 0.4, 0.6, 0.9, 1.2, 1.4, 1.5, 1.5,
    1.4, 1.4, 1.35, 1.3, 1.3, 1.35, 1.4, 1.3, 1.1, 0.9, 0.7, 0.6,
)

# Relative rate for each day of the week (0 = Monday).
WEEKDAY_PATTERN = (1.15, 1.05, 1.0, 1.0, 1.0, 0.9, 0.9)

COMPLAINTS = {
    1: ["Cardiac arrest", "Major trauma", "Respiratory failure"],
    2: ["Chest pain", "Stroke symptoms", "Suspected sepsis", "Severe shortness of breath"],
    3: ["Abdominal pain", "High fever", "Fall with injury", "Pneumonia symptoms"],
    4: ["Minor fracture", "Deep cut", "Urinary infection"],
    5: ["Sprained ankle", "Skin rash", "Minor cut"],
}


@dataclass(frozen=True)
class SimulationConfig:
    ed_arrivals_per_hour: float = 1.5
    elective_admissions_per_day: float = 1.0
    hourly_pattern: tuple = HOURLY_PATTERN
    weekday_pattern: tuple = WEEKDAY_PATTERN
    triage_probabilities: tuple = (0.02, 0.13, 0.45, 0.30, 0.10)
        # triage level -> (probability of ICU, probability of ward); everyone else goes home from the ED.
    # Assumption, tuned so that occupancy is about 80% (eICU has no ED data).
    ed_disposition: dict = field(default_factory=lambda: {
        1: (0.70, 0.25), 2: (0.35, 0.45), 3: (0.07, 0.12), 4: (0.0, 0.03), 5: (0.0, 0.0),
    })

    # Lengths of stay: (median hours, spread) of a lognormal distribution
    ed_stay: tuple = (3.0, 0.5)
    # Source for the next four values: eICU-CRD Demo v2.0.1 (2,520 ICU stays),
    # notebook ml/notebooks/01_simulator_calibration.ipynb
    icu_stay: tuple = (35.1, 1.05)
    ward_stay: tuple = (59.9, 1.11)
    icu_step_down_probability: float = 0.75
    icu_mortality: float = 0.05

    ward_mortality: float = 0.01
    cleaning_minutes: tuple = (45, 90)
    boarding_retry_minutes: float = 30
    name_locale: str = "en_IN"
        # Vital signs
    deterioration_probability: float = 0.10
    deterioration_onset_hours: tuple = (6, 48)
    deterioration_hours_to_peak: float = 12
    recovery_hours: float = 24
    reading_interval_minutes: dict = field(default_factory=lambda: {"ED": 30, "ICU": 15, "WARD": 60})
    temperature_interval_hours: float = 4
    # Equipment
    telemetry_interval_minutes: float = 10
    faults_per_device_per_day: float = 1 / 60
    fault_hours_to_failure: tuple = (12, 36)
