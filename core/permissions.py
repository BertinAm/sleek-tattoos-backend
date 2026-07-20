from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsStaffOrReadOnly(BasePermission):
    """Anyone can GET; only authenticated staff (the admin panel) can write.
    Matches the current frontend's public-site-reads / admin-panel-writes split."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsStaffOnly(BasePermission):
    """For endpoints with no public read at all (e.g. logs, bookings list, contacts list)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
