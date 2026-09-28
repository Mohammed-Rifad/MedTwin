from django.contrib import admin
from django.db.models import Count, Q
from .models import Admission, Bed, EmergencyArrival, Patient, Transfer, Unit, VitalReading
from .models import Bed, Patient, Unit


class BedInline(admin.TabularInline):
    model = Bed
    extra = 0
    fields = ("code", "status", "is_active", "map_x", "map_y")


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "unit_type", "floor", "bed_total", "bed_occupied")
    list_filter = ("unit_type", "floor")
    inlines = [BedInline]

    def get_queryset(self, request):
        active = Q(beds__is_active=True)
        return super().get_queryset(request).annotate(
            _bed_total=Count("beds", filter=active),
            _bed_occupied=Count("beds", filter=active & Q(beds__status=Bed.Status.OCCUPIED)),
        )

    @admin.display(description="Beds", ordering="_bed_total")
    def bed_total(self, obj):
        return obj._bed_total

    @admin.display(description="Occupied", ordering="_bed_occupied")
    def bed_occupied(self, obj):
        return obj._bed_occupied


@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ("code", "unit", "status", "is_active")
    list_filter = ("unit", "status", "is_active")
    search_fields = ("code",)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("mrn", "full_name", "sex", "age", "created_at")
    list_filter = ("sex",)
    search_fields = ("mrn", "first_name", "last_name")
    readonly_fields = ("mrn", "created_at")


class TransferInline(admin.TabularInline):
    model = Transfer
    extra = 0
    can_delete = False
    readonly_fields = ("from_bed", "to_bed", "transferred_at", "transferred_by")


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ("patient", "bed", "admitted_at", "discharged_at", "outcome", "risk_level")
    list_filter = ("bed__unit", "outcome", "risk_level")
    search_fields = ("patient__mrn", "patient__first_name", "patient__last_name")
    list_select_related = ("patient", "bed")
    inlines = [TransferInline]

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]


@admin.register(VitalReading)
class VitalReadingAdmin(admin.ModelAdmin):
    list_display = ("admission", "recorded_at", "heart_rate", "spo2", "respiratory_rate", "temperature", "source")
    list_filter = ("source",)
    list_select_related = ("admission__patient", "admission__bed")


@admin.register(EmergencyArrival)
class EmergencyArrivalAdmin(admin.ModelAdmin):
    list_display = ("patient", "triage_level", "complaint", "arrived_at", "status")
    list_filter = ("status", "triage_level")
    list_select_related = ("patient",)
