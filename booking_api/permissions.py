from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrOwner(BasePermission):
    """
    Custom permission to only allow owner of an object or admin users to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # ALlow safe methods for all users
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff or obj.user == request.user