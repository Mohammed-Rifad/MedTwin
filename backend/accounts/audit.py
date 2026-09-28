from .models import AuditLog


def log_action(request, action, obj=None, description=""):
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        object_type=obj._meta.label if obj is not None else "",
        object_id=str(obj.pk) if obj is not None else "",
        description=description,
        ip_address=request.META.get("REMOTE_ADDR"),
    )
