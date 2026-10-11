import django_filters
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from accounts.audit import log_action
from accounts.models import AuditLog
from accounts.permissions import IsAdminRole

from . import rules, services
from .models import Alert
from .serializers import AlertSerializer, ThresholdSerializer


class AlertFilter(django_filters.FilterSet):
    active = django_filters.BooleanFilter(method="filter_active")

    class Meta:
        model = Alert
        fields = ["status", "severity", "kind", "admission", "equipment", "unit"]

    def filter_active(self, queryset, name, value):
        if value:
            return queryset.exclude(status=Alert.Status.RESOLVED)
        return queryset.filter(status=Alert.Status.RESOLVED)


class AlertViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Alerts are created by the system. People can only acknowledge and resolve them."""

    queryset = Alert.objects.select_related(
        "admission__bed", "equipment", "unit", "acknowledged_by", "resolved_by"
    )
    serializer_class = AlertSerializer
    filterset_class = AlertFilter
    search_fields = ["message"]
    ordering_fields = ["created_at", "last_seen_at", "severity"]

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        alert = services.acknowledge_alert(alert=self.get_object(), by=request.user)
        log_action(request, AuditLog.Action.UPDATE, alert, "Acknowledged alert")
        return Response(self.get_serializer(alert).data)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        alert = services.resolve_alert(alert=self.get_object(), by=request.user)
        log_action(request, AuditLog.Action.UPDATE, alert, "Resolved alert")
        return Response(self.get_serializer(alert).data)


def threshold_data(key):
    rule = rules.get_rule(key)
    override = rules.overrides().get(key)
    return {
        "key": key,
        "name": rule.name,
        "kind": rule.kind,
        "unit": rule.unit.strip(),
        "direction": rule.direction,
        "warning": rule.warning,
        "critical": rule.critical,
        "clear": rule.clear,
        "is_default": override is None,
        "updated_at": override.updated_at if override else None,
        "updated_by": override.updated_by.username if override and override.updated_by else None,
    }


class ThresholdViewSet(viewsets.ViewSet):
    """Admins can view and change each alert rule's limits, or reset them to the defaults."""

    permission_classes = [IsAdminRole]
    serializer_class = ThresholdSerializer
    lookup_field = "key"
    lookup_value_regex = "[^/]+"

    def _check_key(self, key):
        if key not in rules.DEFAULT_RULES:
            raise NotFound(f"Unknown rule: {key}.")

    def list(self, request):
        data = [threshold_data(key) for key in rules.DEFAULT_RULES]
        return Response(ThresholdSerializer(data, many=True).data)

    def retrieve(self, request, key=None):
        self._check_key(key)
        return Response(ThresholdSerializer(threshold_data(key)).data)

    def partial_update(self, request, key=None):
        self._check_key(key)
        current = threshold_data(key)
        incoming = ThresholdSerializer(data={**current, **request.data})
        incoming.is_valid(raise_exception=True)
        services.set_threshold(key=key, by=request.user, **incoming.validated_data)
        log_action(request, AuditLog.Action.UPDATE, description=f"Changed alert limits for {key}")
        return Response(ThresholdSerializer(threshold_data(key)).data)

    @action(detail=True, methods=["post"])
    def reset(self, request, key=None):
        self._check_key(key)
        services.reset_threshold(key=key)
        log_action(request, AuditLog.Action.UPDATE, description=f"Reset alert limits for {key}")
        return Response(ThresholdSerializer(threshold_data(key)).data)
