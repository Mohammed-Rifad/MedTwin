import uuid
from datetime import date

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
