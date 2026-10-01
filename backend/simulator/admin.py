from django.contrib import admin

from .models import InjectedFault, PatientPhysiology


@admin.register(PatientPhysiology)
class PatientPhysiologyAdmin(admin.ModelAdmin):
    list_display = ("admission", "deterioration_onset_at", "escalated_at", "last_reading_at")
    list_filter = (("deterioration_onset_at", admin.EmptyFieldListFilter),)
    list_select_related = ("admission__patient", "admission__bed")


@admin.register(InjectedFault)
class InjectedFaultAdmin(admin.ModelAdmin):
    list_display = ("equipment", "started_at", "hours_to_failure", "failed_at", "cleared_at")
    list_select_related = ("equipment",)
