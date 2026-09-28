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


def role_required(*roles):
    class HasRole(BasePermission):
        message = "This action is only allowed for: " + ", ".join(role.label for role in roles)

        def has_permission(self, request, view):
            return request.user.is_authenticated and request.user.role in roles

    return HasRole


class RolePermissionMixin:
    """Lets a ViewSet declare which roles may perform each action."""

    action_roles = {}

    def get_permissions(self):
        roles = self.action_roles.get(self.action)
        if roles:
            return [role_required(*roles)()]
        return super().get_permissions()
