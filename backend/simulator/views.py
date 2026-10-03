from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from twin import clock, events
from accounts.audit import log_action
from accounts.models import AuditLog
from accounts.permissions import IsAdminRole
from config.errors import DomainError
from equipment.models import Equipment
from hospital.models import Admission, EmergencyArrival
from twin import clock
from twin.models import HospitalClock

from .engine import Simulator
from .models import InjectedFault


def clock_status():
    hospital_clock = HospitalClock.load()
    heartbeat = hospital_clock.heartbeat_at
    return {
        "hospital_time": hospital_clock.now(),
        "running": hospital_clock.running,
        "speed": hospital_clock.speed,
        "simulator_process_running": heartbeat is not None and timezone.now() - heartbeat < timedelta(seconds=5),
    }


class StartSerializer(serializers.Serializer):
    speed = serializers.FloatField(min_value=1, max_value=36000, required=False)


class SurgeSerializer(serializers.Serializer):
    patients = serializers.IntegerField(min_value=1, max_value=50)
    triage_level = serializers.ChoiceField(choices=EmergencyArrival.Triage.choices, required=False)


class DeteriorateSerializer(serializers.Serializer):
    admission = serializers.PrimaryKeyRelatedField(queryset=Admission.objects.filter(discharged_at__isnull=True))


class DeviceFaultSerializer(serializers.Serializer):
    equipment = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.filter(status__in=[Equipment.Status.OK, Equipment.Status.WARNING])
    )


@api_view(["GET"])
@permission_classes([IsAdminRole])
def simulator_status(request):
    return Response(clock_status())


@api_view(["POST"])
@permission_classes([IsAdminRole])
def start(request):
    data = StartSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    HospitalClock.load().start(speed=data.validated_data.get("speed"))
    events.clock_ticked(HospitalClock.load())
    return Response(clock_status())


@api_view(["POST"])
@permission_classes([IsAdminRole])
def pause(request):
    HospitalClock.load().pause()
    events.clock_ticked(HospitalClock.load())
    return Response(clock_status())


@api_view(["POST"])
@permission_classes([IsAdminRole])
def surge(request):
    data = SurgeSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    Simulator().create_surge(clock.now(), **data.validated_data)
    log_action(request, AuditLog.Action.CREATE, description=f"Simulated surge of {data.validated_data['patients']} patients")
    return Response(status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAdminRole])
def deteriorate(request):
    data = DeteriorateSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    admission = data.validated_data["admission"]
    Simulator().vitals.start_deterioration(admission, clock.now())
    log_action(request, AuditLog.Action.UPDATE, admission, "Simulated deterioration started")
    return Response(status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAdminRole])
def device_fault(request):
    data = DeviceFaultSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    equipment = data.validated_data["equipment"]
    if InjectedFault.objects.filter(equipment=equipment, failed_at__isnull=True, cleared_at__isnull=True).exists():
        raise DomainError(f"{equipment.code} already has a developing fault.")
    Simulator().devices.start_fault(equipment, clock.now())
    log_action(request, AuditLog.Action.UPDATE, equipment, "Simulated fault started")
    return Response(status=status.HTTP_201_CREATED)
