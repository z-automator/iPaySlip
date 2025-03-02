from django.db import models
from django.urls import reverse
from django.utils import timezone
from employees.models import Employee
from django.core.exceptions import ValidationError
from django.conf import settings

class PayrollPeriod(models.Model):
    """Model for defining payroll periods"""
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    payment_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.start_date.strftime('%d/%m/%Y')} - {self.end_date.strftime('%d/%m/%Y')})"
    
    class Meta:
        ordering = ['-start_date']

class PayrollItem(models.Model):
    """Abstract base class for earnings and deductions"""
    EARNING = 'earning'
    DEDUCTION = 'deduction'
    ITEM_TYPE_CHOICES = [
        (EARNING, 'Earning'),
        (DEDUCTION, 'Deduction'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    class Meta:
        abstract = True

class StandardPayrollItem(PayrollItem):
    """Standard payroll items like taxes, benefits, etc."""
    is_taxable = models.BooleanField(default=False)
    calculation_method = models.CharField(
        max_length=20,
        choices=[
            ('percentage', 'Percentage'),
            ('fixed', 'Fixed Amount'),
        ],
        default='fixed'
    )
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['name']

class Payroll(models.Model):
    """Main payroll model for employees"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payrolls')
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='payrolls')
    
    # Financial information
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Status and dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    processed_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-period__payment_date']
        unique_together = ['employee', 'period']
    
    def __str__(self):
        return f"Payroll for {self.employee} - {self.period}"
    
    def get_absolute_url(self):
        return reverse('payroll_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        # Calculate net salary
        self.net_salary = self.gross_salary - self.total_deductions
        
        # Set processed date if completed
        if self.status == self.COMPLETED and not self.processed_date:
            self.processed_date = timezone.now()
            
        super().save(*args, **kwargs)

class PayrollEntry(models.Model):
    """Individual payroll entries (earnings or deductions)"""
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='entries')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_deduction = models.BooleanField(default=False)
    
    def __str__(self):
        entry_type = "Deduction" if self.is_deduction else "Earning"
        return f"{self.name} ({entry_type}): {self.amount}"
    
    class Meta:
        ordering = ['-is_deduction', 'name']
        verbose_name_plural = "Payroll entries"

class TaxTier(models.Model):
    """Model to store income tax tiers/brackets"""
    name = models.CharField(max_length=100)
    min_income = models.DecimalField(
        max_digits=settings.MAX_DIGITS, 
        decimal_places=settings.DECIMAL_PLACES,
        help_text="Minimum income for this tax bracket"
    )
    max_income = models.DecimalField(
        max_digits=settings.MAX_DIGITS, 
        decimal_places=settings.DECIMAL_PLACES,
        help_text="Maximum income for this tax bracket (0 for no upper limit)",
        default=0
    )
    rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Tax rate as a percentage (e.g., 15.00 for 15%)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['min_income']
        verbose_name = "Tax Tier"
        verbose_name_plural = "Tax Tiers"
    
    def __str__(self):
        if self.max_income > 0:
            return f"{self.name}: {self.min_income} to {self.max_income} ({self.rate}%)"
        return f"{self.name}: {self.min_income}+ ({self.rate}%)"
    
    def clean(self):
        """Validate the tax tier"""
        if self.min_income < 0:
            raise ValidationError("Minimum income cannot be negative")
        if self.max_income < 0:
            raise ValidationError("Maximum income cannot be negative")
        if self.max_income > 0 and self.min_income >= self.max_income:
            raise ValidationError("Minimum income must be less than maximum income")
        if self.rate < 0 or self.rate > 100:
            raise ValidationError("Tax rate must be between 0 and 100")
            
        # Check for overlapping tiers
        overlapping_tiers = TaxTier.objects.filter(is_active=True)
        if self.pk:
            overlapping_tiers = overlapping_tiers.exclude(pk=self.pk)
        
        # Check for overlaps with other tiers
        for tier in overlapping_tiers:
            # If this tier has no upper limit (max_income = 0)
            if self.max_income == 0:
                if tier.max_income == 0 or tier.max_income > self.min_income:
                    raise ValidationError(f"This tier overlaps with {tier}")
            # If the other tier has no upper limit
            elif tier.max_income == 0:
                if self.max_income == 0 or self.max_income > tier.min_income:
                    raise ValidationError(f"This tier overlaps with {tier}")
            # Both tiers have upper limits
            else:
                if (self.min_income <= tier.max_income and 
                    self.max_income >= tier.min_income):
                    raise ValidationError(f"This tier overlaps with {tier}")
