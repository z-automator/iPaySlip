from django.db import models
from django.urls import reverse
from django.utils import timezone
from employees.models import Employee

class LoanType(models.Model):
    """Loan types with predefined parameters"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, editable=False)  # Always 0, kept for backward compatibility
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_term_months = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name}"

class Loan(models.Model):
    """Employee loan model"""
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    ACTIVE = 'active'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending Approval'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (ACTIVE, 'Active'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='loans')
    loan_type = models.ForeignKey(LoanType, on_delete=models.SET_NULL, null=True, related_name='loans')
    
    # Loan details
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, editable=False)  # Always 0, kept for backward compatibility
    term_months = models.PositiveIntegerField()
    monthly_payment = models.DecimalField(max_digits=12, decimal_places=2)
    total_payable = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Status and dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    request_date = models.DateField(default=timezone.now)
    approval_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    expected_end_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    
    # Reason and notes
    purpose = models.TextField()
    rejection_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-request_date']
    
    def __str__(self):
        return f"Loan for {self.employee} - {self.amount}"
    
    def get_absolute_url(self):
        return reverse('loan_detail', kwargs={'pk': self.pk})
    
    def calculate_monthly_payment(self):
        """Calculate monthly payment amount (no interest)"""
        # No interest - just divide total by number of months
        return self.amount / self.term_months
    
    def save(self, *args, **kwargs):
        # Ensure interest rate is always 0
        self.interest_rate = 0
        
        # Calculate monthly payment if not manually set
        if not self.monthly_payment:
            self.monthly_payment = self.calculate_monthly_payment()
        
        # Calculate total payable amount (same as amount since no interest)
        if not self.total_payable:
            self.total_payable = self.amount
        
        # Set approval date when approved
        if self.status == self.APPROVED and not self.approval_date:
            self.approval_date = timezone.now().date()
            
        # Set start date and expected end date when active
        if self.status == self.ACTIVE and not self.start_date:
            self.start_date = timezone.now().date()
            self.expected_end_date = self.start_date.replace(
                month=self.start_date.month + self.term_months
            )
        
        # Set actual end date when completed
        if self.status == self.COMPLETED and not self.actual_end_date:
            self.actual_end_date = timezone.now().date()
            
        super().save(*args, **kwargs)

    @property
    def is_fully_paid(self):
        """Check if all loan payments are paid"""
        # If loan is completed, it's fully paid
        if self.status == self.COMPLETED:
            return True
            
        # If there are no payments, it's not fully paid
        if not self.payments.exists():
            return False
            
        # Check if all payments are paid
        return self.payments.filter(is_paid=False).count() == 0
    
    def get_next_payment(self):
        """Get the next unpaid payment"""
        return self.payments.filter(is_paid=False).order_by('payment_date').first()

class LoanPayment(models.Model):
    """Individual loan repayment installments"""
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='payments')
    payment_number = models.PositiveIntegerField(default=1)
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Payment source
    MANUAL = 'manual'
    PAYROLL = 'payroll'
    
    PAYMENT_SOURCE_CHOICES = [
        (MANUAL, 'Manual Payment'),
        (PAYROLL, 'Payroll Deduction'),
    ]
    payment_source = models.CharField(max_length=20, choices=PAYMENT_SOURCE_CHOICES, default=PAYROLL)
    payroll_reference = models.CharField(max_length=100, blank=True)
    
    # Link to payroll if paid through payroll
    payroll = models.ForeignKey('payroll.Payroll', on_delete=models.SET_NULL, null=True, blank=True, related_name='loan_payments')
    
    def __str__(self):
        status = "Paid" if self.is_paid else "Pending"
        return f"Payment {self.payment_number} for {self.loan.employee} - {self.payment_date} ({status})"
    
    class Meta:
        ordering = ['payment_date']
        
    def save(self, *args, **kwargs):
        # Set paid date when marked as paid
        if self.is_paid and not self.paid_date:
            self.paid_date = timezone.now().date()
            
        super().save(*args, **kwargs)
