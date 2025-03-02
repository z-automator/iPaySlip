from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import uuid

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
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
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
