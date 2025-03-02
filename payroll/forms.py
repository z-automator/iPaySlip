from django import forms
from django.core.exceptions import ValidationError
from .models import PayrollPeriod, StandardPayrollItem, Payroll, PayrollEntry, TaxTier

class PayrollPeriodForm(forms.ModelForm):
    class Meta:
        model = PayrollPeriod
        fields = ['name', 'start_date', 'end_date', 'payment_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        payment_date = cleaned_data.get('payment_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Start date must be before end date")
        
        if end_date and payment_date and payment_date < end_date:
            raise ValidationError("Payment date should be on or after the end date")
            
        return cleaned_data

class StandardPayrollItemForm(forms.ModelForm):
    class Meta:
        model = StandardPayrollItem
        fields = ['name', 'description', 'type', 'is_taxable', 'calculation_method', 'value', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['is_taxable'].help_text = "Indicates if this item is subject to tax calculations"
        
class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = ['employee', 'period', 'gross_salary', 'total_deductions', 'net_salary', 'status']
        widgets = {
            'period': forms.Select(attrs={'class': 'form-select'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If this is a new payroll, only allow pending status
        if not self.instance.pk:
            self.fields['status'].choices = [(Payroll.PENDING, 'Pending')]
            # For new payrolls, make salary fields editable
            self.fields['gross_salary'].widget = forms.NumberInput(attrs={'class': 'form-control'})
            self.fields['total_deductions'].widget = forms.NumberInput(attrs={'class': 'form-control'})
            self.fields['net_salary'].widget = forms.NumberInput(attrs={'class': 'form-control', 'readonly': True})
            # Add help text
            self.fields['gross_salary'].help_text = "Enter the gross salary amount"
            self.fields['total_deductions'].help_text = "Enter the total deductions amount"
            self.fields['net_salary'].help_text = "Net salary will be calculated automatically"
        else:
            # For existing payrolls, make salary fields read-only
            self.fields['gross_salary'].widget = forms.NumberInput(attrs={'readonly': True, 'class': 'form-control'})
            self.fields['total_deductions'].widget = forms.NumberInput(attrs={'readonly': True, 'class': 'form-control'})
            self.fields['net_salary'].widget = forms.NumberInput(attrs={'readonly': True, 'class': 'form-control'})
        
        # Add help text
        self.fields['period'].help_text = "Select the payroll period"
        self.fields['employee'].help_text = "Select the employee"
        
    def clean(self):
        cleaned_data = super().clean()
        gross_salary = cleaned_data.get('gross_salary')
        total_deductions = cleaned_data.get('total_deductions')
        
        # Calculate net salary
        if gross_salary is not None and total_deductions is not None:
            cleaned_data['net_salary'] = gross_salary - total_deductions
            
        return cleaned_data

class PayrollEntryForm(forms.ModelForm):
    class Meta:
        model = PayrollEntry
        fields = ['name', 'description', 'amount', 'is_deduction']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        
class PayrollProcessForm(forms.Form):
    """Form for batch processing payrolls"""
    period = forms.ModelChoiceField(
        queryset=PayrollPeriod.objects.filter(is_active=True),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    include_all_active_employees = forms.BooleanField(
        initial=True, 
        required=False,
        help_text="Generate payrolls for all active employees",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update the queryset to only include active periods
        self.fields['period'].queryset = PayrollPeriod.objects.filter(is_active=True).order_by('-start_date')
        self.fields['period'].help_text = "Select the payroll period to process"

class TaxTierForm(forms.ModelForm):
    class Meta:
        model = TaxTier
        fields = ['name', 'min_income', 'max_income', 'rate', 'is_active']
        widgets = {
            'min_income': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_income': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['max_income'].help_text = "Enter 0 for no upper limit (highest tax bracket)"
        self.fields['rate'].help_text = "Enter the percentage rate (e.g., 15 for 15%)" 