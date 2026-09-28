from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminRole(BasePermission):
    message = "Only admins can perform this action."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin_role


class IsDoctor(BasePermission):
    message = "Only doctors can perform this action."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == request.user.Role.DOCTOR


class IsClinicalStaff(BasePermission):
    message = "Only doctors and nurses can perform this action."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_clinical


class IsAdminOrReadOnly(BasePermission):
    message = "Only admins can make changes."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.method in SAFE_METHODS or request.user.is_admin_role
