from django.contrib import admin
from .models import LoanType, Loan, LoanPayment
from django.utils import timezone

@admin.register(LoanType)
class LoanTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'interest_rate', 'max_amount', 'max_term_months', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

class LoanPaymentInline(admin.TabularInline):
    model = LoanPayment
    extra = 0
    fields = ('payment_date', 'amount', 'is_paid', 'paid_date', 'payment_source', 'payroll_reference')
    readonly_fields = ('paid_date',)

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        'employee', 'loan_type', 'amount', 'monthly_payment', 
        'term_months', 'status', 'request_date'
    )
    list_filter = ('status', 'loan_type', 'request_date')
    search_fields = (
        'employee__first_name', 'employee__last_name', 
        'employee__employee_id', 'purpose'
    )
    readonly_fields = (
        'approval_date', 'start_date', 'expected_end_date', 
        'actual_end_date', 'created_at', 'updated_at'
    )
    date_hierarchy = 'request_date'
    inlines = [LoanPaymentInline]
    
    fieldsets = (
        ('Employee & Loan Type', {
            'fields': ('employee', 'loan_type')
        }),
        ('Loan Details', {
            'fields': ('amount', 'interest_rate', 'term_months', 'monthly_payment', 'total_payable')
        }),
        ('Status & Dates', {
            'fields': (
                'status', 'request_date', 'approval_date', 
                'start_date', 'expected_end_date', 'actual_end_date'
            )
        }),
        ('Purpose & Notes', {
            'fields': ('purpose', 'rejection_reason', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if obj.status == Loan.APPROVED and not obj.approval_date:
            obj.approval_date = timezone.now().date()
        super().save_model(request, obj, form, change)

@admin.register(LoanPayment)
class LoanPaymentAdmin(admin.ModelAdmin):
    list_display = ('loan', 'payment_date', 'amount', 'is_paid', 'paid_date', 'payment_source')
    list_filter = ('is_paid', 'payment_source', 'payment_date')
    search_fields = (
        'loan__employee__first_name', 'loan__employee__last_name', 
        'loan__employee__employee_id', 'notes'
    )
    readonly_fields = ('paid_date',)
    date_hierarchy = 'payment_date'
    list_select_related = ('loan', 'loan__employee')
