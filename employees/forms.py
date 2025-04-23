from django import forms
from django.contrib.auth.models import User
from .models import Employee, Department
from payroll.models import Currency

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
    email = forms.EmailField(
        max_length=254, 
        required=True,
        help_text="Employee's email address for system access"
    )
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
            'salary_type': forms.Select(attrs={'class': 'form-select', 'onchange': 'toggleSalaryFields(this.value)'}),
            'salary_currency': forms.Select(attrs={'class': 'form-select'}),
            'base_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make some fields optional
        optional_fields = ['end_date', 'profile_image', 'phone_number', 'base_salary', 'hourly_rate']
        for field in optional_fields:
            if field in self.fields:
                self.fields[field].required = False
            
        # Add helper text
        self.fields['bank_account'].help_text = "Bank account number for salary transfers"
        self.fields['position'].help_text = "Employee job position/title"
        self.fields['base_salary'].help_text = "Monthly base salary amount (for monthly salary type)"
        self.fields['hourly_rate'].help_text = "Hourly rate amount (for hourly rate type)"
        self.fields['salary_type'].help_text = "Choose between monthly salary or hourly rate"
        self.fields['salary_currency'].help_text = "Select the currency for salary/hourly rate"
        
        # Set up currency field
        self.fields['salary_currency'].queryset = Currency.objects.all().order_by('code')
        self.fields['salary_currency'].label_from_instance = lambda obj: f"{obj.code} - {obj.name} ({obj.symbol})"
        
        # If no currency is selected and we have EGP, set it as default
        if not self.initial.get('salary_currency'):
            try:
                egp_currency = Currency.objects.get(code='EGP')
                self.initial['salary_currency'] = egp_currency.id
            except Currency.DoesNotExist:
                pass
        
        # If this is an existing employee, populate the first_name, last_name, and email fields
        if self.instance and self.instance.pk and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            # Set the initial value of is_active from the instance
            self.fields['is_active'].initial = self.instance.is_active
    
    def clean(self):
        cleaned_data = super().clean()
        salary_type = cleaned_data.get('salary_type')
        base_salary = cleaned_data.get('base_salary')
        hourly_rate = cleaned_data.get('hourly_rate')
        salary_currency = cleaned_data.get('salary_currency')
        email = cleaned_data.get('email')
        
        if not salary_currency:
            self.add_error('salary_currency', 'Please select a currency')
        
        if salary_type == 'monthly' and not base_salary:
            self.add_error('base_salary', 'Base salary is required for monthly salary type')
        elif salary_type == 'hourly' and not hourly_rate:
            self.add_error('hourly_rate', 'Hourly rate is required for hourly rate type')
        
        # Check if email is unique among users (except for the current user if editing)
        if email:
            user_with_email = User.objects.filter(email=email)
            if self.instance and self.instance.pk and self.instance.user:
                user_with_email = user_with_email.exclude(pk=self.instance.user.pk)
            if user_with_email.exists():
                self.add_error('email', 'This email is already in use by another user')
        
        return cleaned_data