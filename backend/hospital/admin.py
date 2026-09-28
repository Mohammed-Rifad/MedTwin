from django.contrib import admin
from django.db.models import Count, Q

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
