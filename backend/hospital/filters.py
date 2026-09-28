import django_filters

from .models import Admission, Patient


class PatientFilter(django_filters.FilterSet):
    admitted = django_filters.BooleanFilter(method="filter_admitted")
    unit = django_filters.NumberFilter(method="filter_unit")
    risk_level = django_filters.CharFilter(method="filter_risk_level")
    admitted_after = django_filters.DateFilter(method="filter_admitted_after")

    class Meta:
        model = Patient
        fields = ["sex"]

    def filter_admitted(self, queryset, name, value):
        active = Admission.objects.filter(discharged_at__isnull=True).values("patient")
        return queryset.filter(pk__in=active) if value else queryset.exclude(pk__in=active)


    def filter_unit(self, queryset, name, value):
        return queryset.filter(
            admissions__discharged_at__isnull=True, admissions__bed__unit=value
        ).distinct()

    def filter_risk_level(self, queryset, name, value):
        return queryset.filter(
            admissions__discharged_at__isnull=True, admissions__risk_level=value
        ).distinct()

    def filter_admitted_after(self, queryset, name, value):
        return queryset.filter(admissions__admitted_at__date__gte=value).distinct()


class AdmissionFilter(django_filters.FilterSet):
    active = django_filters.BooleanFilter(field_name="discharged_at", lookup_expr="isnull")
    unit = django_filters.NumberFilter(field_name="bed__unit")

    class Meta:
        model = Admission
        fields = ["patient", "risk_level"]
