from rest_framework.permissions import BasePermission
from .models import UserRole

# Roles that have the same privileges as Company Admin (plus their own extras).
_ADMIN_ROLES = (UserRole.SUPER_ADMIN, UserRole.COMPANY_ADMIN)


class IsSuperAdmin(BasePermission):
    """Grants access only to SUPER_ADMIN — used for hard-delete endpoints."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    request.user.role == UserRole.SUPER_ADMIN)


class IsCompanyAdmin(BasePermission):
    """Grants access to COMPANY_ADMIN and SUPER_ADMIN."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    request.user.role in _ADMIN_ROLES)


class IsCheckerOrAdmin(BasePermission):
    """Grants access to CHECKER, COMPANY_ADMIN, and SUPER_ADMIN."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    request.user.role in (UserRole.CHECKER, *_ADMIN_ROLES))


class IsAnyRole(BasePermission):
    """Grants access to any authenticated user regardless of role."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsDocumentOwner(BasePermission):
    """
    Object-level permission: grants write access only to the Maker who created the document.
    The view must call self.get_object() before this is evaluated.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return request.user and request.user.is_authenticated
        return bool(request.user and request.user.is_authenticated and
                    obj.created_by_id == request.user.id)
