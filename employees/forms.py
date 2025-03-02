from django import forms
from django.contrib.auth.models import User
from .models import Employee, Department

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        
class EmployeeForm(forms.ModelForm):
    # Add first name and last name fields that aren't part of the Employee model
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label="Link to existing user account",
        help_text="Optional: Select an existing user account to link to this employee"
    )
    # Explicitly define is_active field with CheckboxInput widget
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Indicates whether the employee is currently active"
    )
    
    class Meta:
        model = Employee
        exclude = ['user', 'created_at', 'updated_at']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'required': False}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make some fields optional
        optional_fields = ['end_date', 'profile_image', 'phone_number']
        for field in optional_fields:
            if field in self.fields:
                self.fields[field].required = False
            
        # Add helper text
        self.fields['bank_account'].help_text = "Bank account number for salary transfers"
        self.fields['position'].help_text = "Employee job position/title"
        self.fields['base_salary'].help_text = "Monthly base salary amount before deductions"
        
        # If this is an existing employee, populate the first_name and last_name fields
        if self.instance and self.instance.pk and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            # Set the initial value of is_active from the instance
            self.fields['is_active'].initial = self.instance.is_active 