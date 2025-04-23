from django.shortcuts import render
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Leave
from .serializers import LeaveSerializer
from .permissions import IsOwnerOrStaff, IsStaffEditorOnly


class LeaveViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing leave requests.
    
    Provides CRUD operations for Leave model with appropriate permissions:
    - List: Staff can see all, regular users only their own
    - Create: Any authenticated user (employee auto-assigned)
    - Retrieve/Update/Delete: Staff can access all, regular users only their own
    - Status field can only be modified by staff users
    """
    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'leave_type', 'start_date', 'end_date']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name', 'reason']
    ordering_fields = ['start_date', 'end_date', 'created_at', 'updated_at']
    ordering = ['-start_date']  # Default ordering
    
    def get_queryset(self):
        """
        This view returns:
        - All leaves for staff users
        - Only the user's own leaves for regular users
        """
        user = self.request.user
        if user.is_staff:
            return Leave.objects.all()
        return Leave.objects.filter(employee=user)
    
    def perform_create(self, serializer):
        """
        Create a new leave request.
        If the user is not staff, automatically set employee to the current user.
        """
        user = self.request.user
        
        # If user is not staff, force employee to be the current user
        if not user.is_staff:
            serializer.save(employee=user)
        else:
            # Staff can create leaves for any employee
            serializer.save()
    
    def update(self, request, *args, **kwargs):
        """
        Update a leave request.
        Apply special permission check for status field.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check if status is being updated by non-staff
        if 'status' in request.data and not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to change the status."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)
