from django.contrib import admin

from .models import HospitalClock


@admin.register(HospitalClock)
class HospitalClockAdmin(admin.ModelAdmin):
    list_display = ("__str__", "anchor_sim_time", "anchor_real_time")
