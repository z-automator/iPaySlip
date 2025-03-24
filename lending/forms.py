from django import forms
from django.core.exceptions import ValidationError
from .models import LoanType, Loan, LoanPayment

class LoanTypeForm(forms.ModelForm):
    class Meta:
        model = LoanType
        fields = ['name', 'description', 'max_amount', 'max_term_months', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['max_amount'].help_text = "Maximum loan amount allowed"
        self.fields['max_term_months'].help_text = "Maximum repayment period in months"

class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = [
            'employee', 'loan_type', 'amount', 
            'term_months', 'purpose', 'notes'
        ]
        widgets = {
            'purpose': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notes'].required = False
        
        # If this is a new loan application, we don't need to show all these fields
        if not self.instance.pk:
            # Hide fields that will be calculated or set automatically
            self.fields['monthly_payment'] = forms.DecimalField(
                widget=forms.HiddenInput(), required=False
            )
            self.fields['total_payable'] = forms.DecimalField(
                widget=forms.HiddenInput(), required=False
            )
        
    def clean(self):
        cleaned_data = super().clean()
        loan_type = cleaned_data.get('loan_type')
        amount = cleaned_data.get('amount')
        term_months = cleaned_data.get('term_months')
        
        if loan_type and amount and amount > loan_type.max_amount:
            raise ValidationError({
                'amount': f"Amount exceeds maximum allowed for this loan type ({loan_type.max_amount})"
            })
            
        if loan_type and term_months and term_months > loan_type.max_term_months:
            raise ValidationError({
                'term_months': f"Term exceeds maximum allowed for this loan type ({loan_type.max_term_months} months)"
            })
            
        return cleaned_data

class LoanApprovalForm(forms.ModelForm):
    """Form for loan approval/rejection process"""
    class Meta:
        model = Loan
        fields = ['status', 'notes', 'rejection_reason']
        widgets = {
            'rejection_reason': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit status choices to approved or rejected
        self.fields['status'].choices = [
            (Loan.APPROVED, 'Approve Loan'),
            (Loan.REJECTED, 'Reject Loan'),
        ]
        self.fields['rejection_reason'].required = False
        self.fields['notes'].required = False
        
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        rejection_reason = cleaned_data.get('rejection_reason')
        
        if status == Loan.REJECTED and not rejection_reason:
            raise ValidationError({
                'rejection_reason': "Rejection reason is required when rejecting a loan application"
            })
            
        return cleaned_data
        
class LoanRepaymentForm(forms.ModelForm):
    class Meta:
        model = LoanPayment
        fields = ['payment_date', 'amount', 'is_paid', 'notes', 'payment_source']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notes'].required = False
        
    def clean(self):
        cleaned_data = super().clean()
        is_paid = cleaned_data.get('is_paid')
        payment_source = cleaned_data.get('payment_source')
        
        if is_paid and payment_source == LoanPayment.PAYROLL:
            # Ensure there's a payroll reference if paid through payroll
            if not cleaned_data.get('payroll_reference'):
                raise ValidationError({
                    'payroll_reference': "Payroll reference is required for payroll deduction payments"
                })
                
        return cleaned_data 