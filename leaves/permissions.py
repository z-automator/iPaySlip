from rest_framework import permissions


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Custom permission to only allow owners of a leave request to view or edit it.
    Staff users can view and edit all leave requests.
    """
    
    def has_permission(self, request, view):
        # Authenticated users can list and create
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Staff can do anything
        if request.user.is_staff:
            return True
            
        # Regular users can only access their own leaves
        return obj.employee == request.user


class IsStaffEditorOnly(permissions.BasePermission):
    """
    Custom permission to only allow staff users to edit certain fields.
    This is used for fields like 'status' that should only be editable by staff.
    """
    
    def has_permission(self, request, view):
        # All authenticated users have read permission
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
            
        # For write operations, check if user is staff
        if request.method in ['PUT', 'PATCH'] and 'status' in request.data:
            return request.user.is_staff
            
        # For other write operations, regular permission checks apply
        return True
    
    def has_object_permission(self, request, view, obj):
        # Staff can do anything
        if request.user.is_staff:
            return True
            
        # Regular users can only access their own leaves
        if obj.employee != request.user:
            return False
            
        # Regular users can't modify status
        if request.method in ['PUT', 'PATCH'] and 'status' in request.data:
            return False
            
        return True
