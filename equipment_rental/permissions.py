from rest_framework.permissions import BasePermission, SAFE_METHODS


ROLE_ADMIN = "admin"
ROLE_FARMER = "farmer"


def get_user_role(user):
    if not user or not user.is_authenticated:
        return ""

    return (
        getattr(user, "role", None)
        or getattr(user, "user_type", None)
        or ""
    ).lower()


def is_admin_user(user):
    return (
        user
        and user.is_authenticated
        and (
            user.is_superuser
            or user.is_staff
            or get_user_role(user) == ROLE_ADMIN
        )
    )


def is_farmer_user(user):
    return (
        user
        and user.is_authenticated
        and get_user_role(user) == ROLE_FARMER
    )


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return is_admin_user(request.user)


class IsFarmerRole(BasePermission):
    def has_permission(self, request, view):
        return is_farmer_user(request.user)


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated

        return is_admin_user(request.user)


class IsFarmerOwnerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if is_admin_user(request.user):
            return True

        return getattr(obj, "farmer_user_id", None) == request.user.id


class CanEditBooking(BasePermission):
    def has_object_permission(self, request, view, obj):
        if is_admin_user(request.user):
            return True

        if getattr(obj, "farmer_user_id", None) != request.user.id:
            return False

        return obj.can_edit()


class CanCancelBooking(BasePermission):
    def has_object_permission(self, request, view, obj):
        if is_admin_user(request.user):
            return True

        if getattr(obj, "farmer_user_id", None) != request.user.id:
            return False

        return obj.can_cancel()