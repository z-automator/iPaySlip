from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Leave


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model (used for nested representation)"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
        read_only_fields = ['id', 'username', 'email', 'full_name']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class LeaveSerializer(serializers.ModelSerializer):
    """
    Serializer for the Leave model.
    
    Handles validation and permissions for leave requests.
    - Regular users can only see and modify their own leaves
    - Staff users can see and modify all leaves
    - Status field is only editable by staff users
    """
    employee = UserSerializer(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(
        source='employee',
        queryset=User.objects.all(),
        write_only=True,
        required=False
    )
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Leave
        fields = [
            'id', 'employee', 'employee_id', 'start_date', 'end_date',
            'leave_type', 'leave_type_display', 'status', 'status_display',
            'reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Custom validation to ensure:
        1. End date is after start date
        2. No overlapping leave dates for the same employee
        """
        # Get the employee (either from data or from context)
        employee = data.get('employee')
        if not employee and self.instance:
            employee = self.instance.employee
        
        # Get start_date and end_date (either from data or from instance)
        start_date = data.get('start_date')
        if not start_date and self.instance:
            start_date = self.instance.start_date
            
        end_date = data.get('end_date')
        if not end_date and self.instance:
            end_date = self.instance.end_date
        
        # Validate end_date > start_date
        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date.'
            })
        
        # Check for overlapping leaves for the same employee
        if employee and start_date and end_date:
            overlapping_leaves = Leave.objects.filter(
                employee=employee,
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            
            # Exclude current instance when updating
            if self.instance:
                overlapping_leaves = overlapping_leaves.exclude(pk=self.instance.pk)
            
            if overlapping_leaves.exists():
                raise serializers.ValidationError(
                    'You already have leave scheduled during this period.'
                )
        
        return data

    def create(self, validated_data):
        """
        Create a new leave request.
        If employee_id is not provided, use the current user.
        """
        request = self.context.get('request')
        
        # If employee not specified and not staff, use current user
        if 'employee' not in validated_data and request and hasattr(request, 'user'):
            if not request.user.is_staff:
                validated_data['employee'] = request.user
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update a leave request.
        Only staff users can update the status field.
        """
        request = self.context.get('request')
        
        # Check if user is trying to update status and is not staff
        if 'status' in validated_data and request and hasattr(request, 'user'):
            if not request.user.is_staff:
                # Remove status from validated_data
                validated_data.pop('status')
        
        return super().update(instance, validated_data)
