from rest_framework.permissions import BasePermission
from .models import UserRole


class IsCompanyAdmin(BasePermission):
    """Grants access only to users with the COMPANY_ADMIN role."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    request.user.role == UserRole.COMPANY_ADMIN)


class IsCheckerOrAdmin(BasePermission):
    """Grants access to CHECKER and COMPANY_ADMIN roles."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    request.user.role in (UserRole.CHECKER, UserRole.COMPANY_ADMIN))


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
