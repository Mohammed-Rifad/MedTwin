from datetime import timedelta

from django.db.models import F

from equipment import services as equipment_services
from equipment.models import Equipment
from hospital.models import Bed
import numpy as np
from .models import InjectedFault

# Normal internal temperature (°C) of each kind of device when idle
BASE_TEMPERATURE = {
    Equipment.Kind.VENTILATOR: 38.0,
    Equipment.Kind.MONITOR: 34.0,
    Equipment.Kind.INFUSION_PUMP: 31.0,
}


class DeviceSimulator:
    def __init__(self, simulator):
        self.sim = simulator
        self.next_reading = {}   # equipment id -> when its next reading is due
        self.running_hours = {}  # equipment id -> running hours so far

    @property
    def config(self):
        return self.sim.config

    def step(self, now):
        self.repair_failed_devices(now)
        self.clear_repaired_faults()
        interval = timedelta(minutes=self.config.telemetry_interval_minutes)
        chance = self.config.faults_per_device_per_day * self.config.telemetry_interval_minutes / 1440
        faults = {
            fault.equipment_id: fault
            for fault in InjectedFault.objects.filter(failed_at__isnull=True, cleared_at__isnull=True)
        }
        devices = Equipment.objects.exclude(
            status__in=[Equipment.Status.MAINTENANCE, Equipment.Status.FAULT]
        ).select_related("bed")

        for device in devices:
            due = self.next_reading.get(device.pk, now)
            while due <= now:
                fault = faults.get(device.pk)
                if fault is None and self.sim.rng.random() < chance:
                    fault = faults[device.pk] = self.start_fault(device, due)
                progress = fault.progress(due) if fault else 0.0
                if progress >= 1.0:
                    self.fail(device, fault, due)
                    break
                self.sim.save_telemetry(device, due, self.reading(device, progress, interval))

                due += interval
            self.next_reading[device.pk] = due

    def reading(self, device, progress, interval):
        rng = self.sim.rng
        in_use = device.bed_id is not None and device.bed.status == Bed.Status.OCCUPIED
        hours = self.running_hours.get(device.pk)
        if hours is None:
            latest = device.readings.first()
            hours = latest.running_hours if latest else float(rng.uniform(500, 20000))
        if in_use:
            hours += interval / timedelta(hours=1)
        self.running_hours[device.pk] = hours

        pressure = None
        if device.kind == Equipment.Kind.VENTILATOR and in_use:
            pressure = round(float(rng.normal(18, 1.5) + progress * rng.normal(0, 6)), 1)
        temperature = BASE_TEMPERATURE[device.kind] + (2.0 if in_use else 0.0) + rng.normal(0, 0.4) + progress * 9
        return {
            "temperature": round(float(temperature), 1),
            "running_hours": round(hours, 1),
            "error_count": int(rng.poisson(0.02 + progress * 1.5)),
            "pressure": pressure,
        }

    def start_fault(self, device, at):
        """Start a fault that will make the device fail in 12-36 hours unless it is serviced."""
        return InjectedFault.objects.create(
            equipment=device,
            started_at=at,
            hours_to_failure=float(self.sim.rng.uniform(*self.config.fault_hours_to_failure)),
        )

    def fail(self, device, fault, at):
        fault.failed_at = at
        fault.save(update_fields=["failed_at"])
        equipment_services.mark_failed(equipment=device)

    def clear_repaired_faults(self):
        repaired = InjectedFault.objects.filter(
            cleared_at__isnull=True,
            equipment__status=Equipment.Status.OK,
            equipment__last_serviced_at__gte=F("started_at"),
        ).select_related("equipment")
        for fault in repaired:
            fault.cleared_at = fault.equipment.last_serviced_at
            fault.save(update_fields=["cleared_at"])
            self.next_reading.pop(fault.equipment_id, None)

    def repair_failed_devices(self, now):
        """The hospital's technicians repair broken machines 24-72 hours after they break."""
        broken = InjectedFault.objects.filter(
            failed_at__isnull=False, cleared_at__isnull=True, equipment__status=Equipment.Status.FAULT
        ).select_related("equipment")
        for fault in broken:
            wait = np.random.default_rng([self.sim.seed, fault.pk]).uniform(*self.config.repair_hours)
            if now >= fault.failed_at + timedelta(hours=wait):
                equipment_services.start_maintenance(
                    equipment=fault.equipment, reason="Repair after failure", at=now - timedelta(hours=2)
                )
                equipment_services.finish_maintenance(
                    equipment=fault.equipment, notes="Repaired by technician", at=now
                )
