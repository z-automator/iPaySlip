from django.db import models
from django.urls import reverse
from django.utils import timezone
from employees.models import Employee
from django.core.exceptions import ValidationError
from django.conf import settings
from decimal import Decimal

class Currency(models.Model):
    """Model for managing different currencies and their exchange rates to EGP"""
    code = models.CharField(max_length=3, unique=True, help_text="Currency code (e.g., USD, EUR)")
    name = models.CharField(max_length=50, help_text="Currency name (e.g., US Dollar)")
    symbol = models.CharField(max_length=5, help_text="Currency symbol (e.g., $)")
    exchange_rate_to_egp = models.DecimalField(
        max_digits=10, 
        decimal_places=4,
        help_text="Exchange rate to convert to EGP (e.g., 1 USD = 30.90 EGP)"
    )
    is_base_currency = models.BooleanField(default=False, help_text="Whether this is the base currency (EGP)")
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Currencies"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one base currency exists
        if self.is_base_currency:
            Currency.objects.filter(is_base_currency=True).exclude(pk=self.pk).update(is_base_currency=False)
            # Base currency (EGP) should always have exchange rate 1
            self.exchange_rate_to_egp = Decimal('1.0')
        super().save(*args, **kwargs)
    
    def convert_to_egp(self, amount):
        """Convert an amount from this currency to EGP"""
        return amount * self.exchange_rate_to_egp
    
    def convert_from_egp(self, amount):
        """Convert an amount from EGP to this currency"""
        return amount / self.exchange_rate_to_egp

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
    
    # Financial information in original currency
    currency = models.ForeignKey(
        Currency, 
        on_delete=models.PROTECT,
        default=1,  # This will be the ID of our base currency (EGP)
        help_text="Currency for this payroll's amounts"
    )
    exchange_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=4,
        default=1.0000,
        help_text="Exchange rate to EGP at the time of payroll creation"
    )
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Financial information in EGP (for reporting consistency)
    gross_salary_egp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions_egp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_salary_egp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
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
        # Set currency and exchange rate from employee if not set
        if not self.currency_id:
            self.currency = self.employee.salary_currency
            self.exchange_rate = self.currency.exchange_rate_to_egp
        
        # Ensure values are not None
        if self.gross_salary is None:
            self.gross_salary = Decimal('0.00')
        
        # Ensure total_deductions is not None
        if self.total_deductions is None:
            self.total_deductions = Decimal('0.00')
        
        # Calculate net salary in original currency
        self.net_salary = self.gross_salary - self.total_deductions
        
        # Set exchange rate to Decimal if it's a float
        if isinstance(self.exchange_rate, float):
            exchange_rate_decimal = Decimal(str(self.exchange_rate))
        else:
            exchange_rate_decimal = self.exchange_rate or Decimal('1.00')
        
        # Calculate amounts in EGP
        self.gross_salary_egp = self.gross_salary * exchange_rate_decimal
        self.total_deductions_egp = self.total_deductions * exchange_rate_decimal
        self.net_salary_egp = self.net_salary * exchange_rate_decimal
        
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
    amount_egp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_deduction = models.BooleanField(default=False)
    
    def __str__(self):
        entry_type = "Deduction" if self.is_deduction else "Earning"
        return f"{self.name} ({entry_type}): {self.amount} {self.payroll.currency.code}"
    
    def save(self, *args, **kwargs):
        # Calculate amount in EGP
        if self.payroll.exchange_rate is not None:
            # Always convert exchange_rate to Decimal for calculation
            if isinstance(self.payroll.exchange_rate, float):
                exchange_rate_decimal = Decimal(str(self.payroll.exchange_rate))
                self.amount_egp = self.amount * exchange_rate_decimal
            else:
                self.amount_egp = self.amount * self.payroll.exchange_rate
        else:
            # Default to same amount if no exchange rate
            self.amount_egp = self.amount
        super().save(*args, **kwargs)
    
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

class EmployeePayrollTemplate(models.Model):
    """Stores historical payroll entries for each employee to speed up payroll creation"""
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='payroll_template')
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payroll template for {self.employee}"
    
    def get_entries(self):
        """Get all template entries for this employee"""
        return self.entries.all()
    
    def update_from_payroll(self, payroll):
        """Update template entries from a payroll"""
        # Clear existing template entries
        self.entries.all().delete()
        
        # Create new template entries from payroll entries
        for entry in payroll.entries.all():
            EmployeePayrollTemplateEntry.objects.create(
                template=self,
                name=entry.name,
                description=entry.description,
                amount=entry.amount,
                is_deduction=entry.is_deduction
            )
    
    @classmethod
    def get_or_create_for_employee(cls, employee):
        """Get or create a template for an employee"""
        template, created = cls.objects.get_or_create(employee=employee)
        return template

class EmployeePayrollTemplateEntry(models.Model):
    """Individual entries in an employee's payroll template"""
    template = models.ForeignKey(EmployeePayrollTemplate, on_delete=models.CASCADE, related_name='entries')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_deduction = models.BooleanField(default=False)
    
    def __str__(self):
        entry_type = "Deduction" if self.is_deduction else "Earning"
        return f"{self.name} ({entry_type}): {self.amount}"
    
    class Meta:
        ordering = ['-is_deduction', 'name']
        verbose_name_plural = "Template entries"
