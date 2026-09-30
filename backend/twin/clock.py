from .models import HospitalClock


def now():
    """Current hospital time. Equals real time until the simulator has been started."""
    return HospitalClock.load().now()
