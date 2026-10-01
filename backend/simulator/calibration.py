import math

from .config import SimulationConfig


def mean_hours(median_and_spread):
    """Average stay. It's a bit more than the median, because a few patients stay very long."""
    median, spread = median_and_spread
    return median * math.exp(spread ** 2 / 2)


def expected_census(config=None):
    """Average number of patients in each unit: arrivals per hour x hours each one stays."""
    c = config or SimulationConfig()

    # How many people come to the ED per hour, on average
    ed_per_hour = c.ed_arrivals_per_hour * (sum(c.hourly_pattern) / 24) * (sum(c.weekday_pattern) / 7)

    # What share of ED patients go to the ICU, and what share to a ward
    triage = list(zip(range(1, 6), c.triage_probabilities))
    p_icu = sum(p * c.ed_disposition[level][0] for level, p in triage)
    p_ward = sum(p * c.ed_disposition[level][1] for level, p in triage)

    # Patients arriving per hour into each unit
    ward_from_ed = ed_per_hour * p_ward
    elective = c.elective_admissions_per_day / 24
    escalations = (ward_from_ed + elective) * c.deterioration_probability
    icu_in = ed_per_hour * p_icu + escalations
    step_down = icu_in * (1 - c.icu_mortality) * c.icu_step_down_probability
    ward_in = ward_from_ed + elective + step_down

    # Little's law: patients = arrivals per hour x hours each one stays
    return {
        "ED": ed_per_hour * mean_hours(c.ed_stay),
        "ICU": icu_in * mean_hours(c.icu_stay),
        "WARD": ward_in * mean_hours(c.ward_stay),
    }
