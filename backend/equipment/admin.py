from django.contrib import admin

from .models import Equipment, EquipmentReading, MaintenanceLog


class MaintenanceLogInline(admin.TabularInline):
    model = MaintenanceLog
    extra = 0
    can_delete = False
    readonly_fields = ("reason", "notes", "started_at", "finished_at", "started_by", "finished_by")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ("code", "kind", "unit", "bed", "status", "last_serviced_at")
    list_filter = ("kind", "status", "unit")
    search_fields = ("code", "model_name")
    list_select_related = ("unit", "bed")
    readonly_fields = ("status", "last_serviced_at", "anomaly_score")
    inlines = [MaintenanceLogInline]


@admin.register(EquipmentReading)
class EquipmentReadingAdmin(admin.ModelAdmin):
    list_display = ("equipment", "recorded_at", "temperature", "running_hours", "error_count", "pressure")
    list_filter = ("equipment__kind",)
    list_select_related = ("equipment",)
