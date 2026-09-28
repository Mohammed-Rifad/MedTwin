import uuid
from datetime import date
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Q
from django.utils import timezone
from django.db import models


class Unit(models.Model):
    class UnitType(models.TextChoices):
        ICU = "ICU", "Intensive Care Unit"
        WARD = "WARD", "General Ward"
        ED = "ED", "Emergency Department"

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    unit_type = models.CharField(max_length=10, choices=UnitType.choices)
    floor = models.PositiveSmallIntegerField(default=1)
    map_x = models.PositiveIntegerField(default=0)
    map_y = models.PositiveIntegerField(default=0)
    map_width = models.PositiveIntegerField(default=200)
    map_height = models.PositiveIntegerField(default=150)

    class Meta:
        ordering = ["floor", "name"]

    def __str__(self):
        return self.name

    @property
    def capacity(self):
        return self.beds.filter(is_active=True).count()

    @property
    def occupied_count(self):
        return self.beds.filter(is_active=True, status=Bed.Status.OCCUPIED).count()


class Bed(models.Model):
    class Status(models.TextChoices):
        FREE = "FREE", "Free"
        OCCUPIED = "OCCUPIED", "Occupied"
        CLEANING = "CLEANING", "Cleaning"

    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="beds")
    code = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.FREE)
    is_active = models.BooleanField(default=True)
    map_x = models.PositiveIntegerField(default=0)
    map_y = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["unit", "code"]
        indexes = [models.Index(fields=["unit", "status"])]

    def __str__(self):
        return self.code


def generate_mrn():
    return f"MRN-{uuid.uuid4().hex[:8].upper()}"


class Patient(models.Model):
    class Sex(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"

    mrn = models.CharField("MRN", max_length=20, unique=True, default=generate_mrn, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    sex = models.CharField(max_length=1, choices=Sex.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.full_name} ({self.mrn})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        today = date.today()
        had_birthday = (today.month, today.day) >= (self.date_of_birth.month, self.date_of_birth.day)
        return today.year - self.date_of_birth.year - (0 if had_birthday else 1)


class Admission(models.Model):
    class Outcome(models.TextChoices):
        HOME = "HOME", "Discharged home"
        TRANSFERRED = "TRANSFERRED", "Transferred to another facility"
        DECEASED = "DECEASED", "Deceased"

    class RiskLevel(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="admissions")
    bed = models.ForeignKey(Bed, on_delete=models.PROTECT, related_name="admissions")
    reason = models.CharField(max_length=255, blank=True)
    admitted_at = models.DateTimeField(default=timezone.now)
    expected_discharge_at = models.DateTimeField(null=True, blank=True)
    discharged_at = models.DateTimeField(null=True, blank=True)
    outcome = models.CharField(max_length=12, choices=Outcome.choices, blank=True)
    risk_score = models.FloatField(null=True, blank=True)
    risk_level = models.CharField(max_length=6, choices=RiskLevel.choices, blank=True)
    admitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    discharged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-admitted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["patient"],
                condition=Q(discharged_at__isnull=True),
                name="one_active_admission_per_patient",
            ),
            models.UniqueConstraint(
                fields=["bed"],
                condition=Q(discharged_at__isnull=True),
                name="one_active_admission_per_bed",
            ),
        ]

    def __str__(self):
        return f"{self.patient.full_name} in {self.bed.code}"

    @property
    def is_active(self):
        return self.discharged_at is None

    @property
    def length_of_stay(self):
        return (self.discharged_at or timezone.now()) - self.admitted_at


class Transfer(models.Model):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name="transfers")
    from_bed = models.ForeignKey(Bed, on_delete=models.PROTECT, related_name="+")
    to_bed = models.ForeignKey(Bed, on_delete=models.PROTECT, related_name="+")
    transferred_at = models.DateTimeField(default=timezone.now)
    transferred_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["transferred_at"]

    def __str__(self):
        return f"{self.from_bed} -> {self.to_bed}"


class VitalReading(models.Model):
    class Source(models.TextChoices):
        MONITOR = "MONITOR", "Bedside monitor"
        MANUAL = "MANUAL", "Manual entry"

    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name="vitals")
    recorded_at = models.DateTimeField(default=timezone.now)
    heart_rate = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(20), MaxValueValidator(250)]
    )
    spo2 = models.PositiveSmallIntegerField(
        "SpO₂ (%)", null=True, blank=True, validators=[MinValueValidator(50), MaxValueValidator(100)]
    )
    systolic_bp = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(40), MaxValueValidator(250)]
    )
    diastolic_bp = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(20), MaxValueValidator(150)]
    )
    respiratory_rate = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(4), MaxValueValidator(60)]
    )
    temperature = models.FloatField(
        "Temperature (°C)", null=True, blank=True, validators=[MinValueValidator(30), MaxValueValidator(45)]
    )
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.MONITOR)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-recorded_at"]
        indexes = [models.Index(fields=["admission", "-recorded_at"])]

    def __str__(self):
        return f"Vitals for {self.admission_id} at {self.recorded_at:%Y-%m-%d %H:%M}"


class EmergencyArrival(models.Model):
    class Triage(models.IntegerChoices):
        RESUSCITATION = 1, "1 - Resuscitation"
        EMERGENT = 2, "2 - Emergent"
        URGENT = 3, "3 - Urgent"
        LESS_URGENT = 4, "4 - Less urgent"
        NON_URGENT = 5, "5 - Non-urgent"

    class Status(models.TextChoices):
        WAITING = "WAITING", "Waiting"
        ADMITTED = "ADMITTED", "Admitted"
        DISCHARGED = "DISCHARGED", "Discharged from ED"

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="emergency_arrivals")
    arrived_at = models.DateTimeField(default=timezone.now)
    triage_level = models.PositiveSmallIntegerField(choices=Triage.choices)
    complaint = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.WAITING)
    admission = models.OneToOneField(
        Admission, null=True, blank=True, on_delete=models.SET_NULL, related_name="emergency_arrival"
    )
    logged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["triage_level", "arrived_at"]

    def __str__(self):
        return f"{self.patient.full_name} (triage {self.triage_level})"
