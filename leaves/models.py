from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class Leave(models.Model):
    """
    Leave model for managing employee leave requests.
    
    This model tracks leave requests with start and end dates, leave types,
    approval status, and reasons. It includes validation to prevent overlapping
    leave dates for the same employee and ensures end date is after start date.
    """
    
    # Leave type choices
    LEAVE_TYPE_CHOICES = [
        ('vacation', _('Vacation')),
        ('sick', _('Sick')),
        ('maternity', _('Maternity')),
        ('paternity', _('Paternity')),
        ('other', _('Other')),
    ]
    
    # Leave status choices
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]
    
    # Foreign key to User model
    employee = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='leaves',
        verbose_name=_('Employee')
    )
    
    # Date fields
    start_date = models.DateField(verbose_name=_('Start Date'))
    end_date = models.DateField(verbose_name=_('End Date'))
    
    # Leave type and status
    leave_type = models.CharField(
        max_length=20,
        choices=LEAVE_TYPE_CHOICES,
        verbose_name=_('Leave Type')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Status')
    )
    
    # Optional reason field
    reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Reason')
    )
    
    # Auto timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = _('Leave')
        verbose_name_plural = _('Leaves')
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date})"
    
    def clean(self):
        """
        Custom validation to ensure:
        1. End date is after start date
        2. No overlapping leave dates for the same employee
        """
        # Validate end_date > start_date
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({
                'end_date': _('End date must be after start date.')
            })
        
        # Check for overlapping leaves for the same employee
        overlapping_leaves = Leave.objects.filter(
            employee=self.employee,
            start_date__lte=self.end_date,
            end_date__gte=self.start_date
        )
        
        # Exclude current instance when updating
        if self.pk:
            overlapping_leaves = overlapping_leaves.exclude(pk=self.pk)
        
        if overlapping_leaves.exists():
            raise ValidationError(
                _('You already have leave scheduled during this period.')
            )
    
    def save(self, *args, **kwargs):
        """Override save method to run validations before saving"""
        self.full_clean()
        super().save(*args, **kwargs)
