from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import uuid
from django.core.exceptions import ValidationError

class Department(models.Model):
    """Department model to categorize employees"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Employee(models.Model):
    """Employee model representing staff members"""
    # Personal Information
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(max_length=36, unique=True, default=uuid.uuid4)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='employee_profiles/', blank=True, null=True)
    
    # Employment Information
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.CharField(max_length=100, blank=True)
    hire_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # Salary Information
    SALARY_TYPE_CHOICES = [
        ('monthly', 'Monthly Salary'),
        ('hourly', 'Hourly Rate'),
    ]
    salary_type = models.CharField(max_length=10, choices=SALARY_TYPE_CHOICES, default='monthly')
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Monthly base salary amount")
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Hourly rate amount")
    salary_currency = models.ForeignKey(
        'payroll.Currency', 
        on_delete=models.PROTECT, 
        related_name='employees',
        default=1,  # This will be the ID of our base currency (EGP)
        help_text="Currency for salary/hourly rate"
    )
    bank_account = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"
    
    def get_absolute_url(self):
        return reverse('employee_detail', kwargs={'pk': self.pk})
    
    @property
    def full_name(self):
        return self.user.get_full_name()
    
    @property
    def email(self):
        return self.user.email
    
    @property
    def base_salary_egp(self):
        """Get base salary converted to EGP"""
        if self.base_salary:
            return self.salary_currency.convert_to_egp(self.base_salary)
        return None
    
    @property
    def hourly_rate_egp(self):
        """Get hourly rate converted to EGP"""
        if self.hourly_rate:
            return self.salary_currency.convert_to_egp(self.hourly_rate)
        return None
    
    def clean(self):
        """Validate that either base_salary or hourly_rate is provided based on salary_type"""
        if self.salary_type == 'monthly' and not self.base_salary:
            raise ValidationError({'base_salary': 'Base salary is required for monthly salary type'})
        elif self.salary_type == 'hourly' and not self.hourly_rate:
            raise ValidationError({'hourly_rate': 'Hourly rate is required for hourly rate type'})
        
        if self.salary_type == 'monthly' and self.hourly_rate:
            self.hourly_rate = None
        elif self.salary_type == 'hourly' and self.base_salary:
            self.base_salary = None
