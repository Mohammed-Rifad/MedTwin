from django.contrib import admin

from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("created_at", "severity", "kind", "message", "status", "last_seen_at")
    list_filter = ("status", "severity", "kind")
    search_fields = ("message", "subject")
    list_select_related = ("admission", "equipment", "unit")

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]
