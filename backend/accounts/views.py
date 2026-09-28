from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .audit import log_action
from .models import AuditLog, User
from .permissions import IsAdminRole
from .serializers import (
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    StaffSerializer,
    UserSerializer,
)


@api_view(["GET"])
def me(request):
    return Response(UserSerializer(request.user).data)


@api_view(["POST"])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    request.user.set_password(serializer.validated_data["new_password"])
    request.user.save(update_fields=["password"])
    log_action(request, AuditLog.Action.UPDATE, request.user, "Changed own password")
    return Response(status=status.HTTP_204_NO_CONTENT)


class StaffViewSet(viewsets.ModelViewSet):
    queryset = User.objects.order_by("username")
    serializer_class = StaffSerializer
    permission_classes = [IsAdminRole]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def perform_create(self, serializer):
        user = serializer.save()
        log_action(self.request, AuditLog.Action.CREATE, user, f"Created {user.role} account")

    def perform_update(self, serializer):
        if serializer.instance == self.request.user:
            data = serializer.validated_data
            if data.get("is_active") is False or data.get("role", User.Role.ADMIN) != User.Role.ADMIN:
                raise ValidationError("You cannot deactivate or demote your own account.")
        user = serializer.save()
        log_action(self.request, AuditLog.Action.UPDATE, user, f"Updated fields: {', '.join(serializer.validated_data)}")

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        user = self.get_object()
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        log_action(request, AuditLog.Action.UPDATE, user, "Password reset by admin")
        return Response(status=status.HTTP_204_NO_CONTENT)


from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .audit import log_action
from .models import AuditLog, User
from .permissions import IsAdminRole
from .serializers import (
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    StaffSerializer,
    UserSerializer,
)


@api_view(["GET"])
def me(request):
    return Response(UserSerializer(request.user).data)


@api_view(["POST"])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    request.user.set_password(serializer.validated_data["new_password"])
    request.user.save(update_fields=["password"])
    log_action(request, AuditLog.Action.UPDATE, request.user, "Changed own password")
    return Response(status=status.HTTP_204_NO_CONTENT)


class StaffViewSet(viewsets.ModelViewSet):
    queryset = User.objects.order_by("username")
    serializer_class = StaffSerializer
    permission_classes = [IsAdminRole]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def perform_create(self, serializer):
        user = serializer.save()
        log_action(self.request, AuditLog.Action.CREATE, user, f"Created {user.role} account")

    def perform_update(self, serializer):
        if serializer.instance == self.request.user:
            data = serializer.validated_data
            if data.get("is_active") is False or data.get("role", User.Role.ADMIN) != User.Role.ADMIN:
                raise ValidationError("You cannot deactivate or demote your own account.")
        user = serializer.save()
        log_action(self.request, AuditLog.Action.UPDATE, user, f"Updated fields: {', '.join(serializer.validated_data)}")

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        user = self.get_object()
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        log_action(request, AuditLog.Action.UPDATE, user, "Password reset by admin")
        return Response(status=status.HTTP_204_NO_CONTENT)
