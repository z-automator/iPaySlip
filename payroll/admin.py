from django.contrib import admin
from .models import PayrollPeriod, StandardPayrollItem, Payroll, PayrollEntry

@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'payment_date', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    date_hierarchy = 'payment_date'

@admin.register(StandardPayrollItem)
class StandardPayrollItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'calculation_method', 'value', 'is_taxable', 'is_active')
    list_filter = ('type', 'is_taxable', 'is_active', 'calculation_method')
    search_fields = ('name', 'description')

class PayrollEntryInline(admin.TabularInline):
    model = PayrollEntry
    extra = 0
    fields = ('name', 'description', 'amount', 'is_deduction')

@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ('employee', 'period', 'gross_salary', 'total_deductions', 'net_salary', 'status', 'processed_date')
    list_filter = ('status', 'period', 'processed_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'processed_date'
    inlines = [PayrollEntryInline]
    
    fieldsets = (
        ('Employee & Period', {
            'fields': ('employee', 'period')
        }),
        ('Salary Details', {
            'fields': ('gross_salary', 'total_deductions', 'net_salary')
        }),
        ('Status', {
            'fields': ('status', 'processed_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
@admin.register(PayrollEntry)
class PayrollEntryAdmin(admin.ModelAdmin):
    list_display = ('payroll', 'name', 'amount', 'is_deduction')
    list_filter = ('is_deduction',)
    search_fields = ('name', 'description', 'payroll__employee__first_name', 'payroll__employee__last_name')
    list_select_related = ('payroll', 'payroll__employee')
