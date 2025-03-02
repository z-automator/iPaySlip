from django.contrib import admin
from .models import Employee, Department

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'employee_id', 'position', 'department', 'is_active', 'base_salary')
    list_filter = ('is_active', 'department')
    search_fields = ('user__first_name', 'user__last_name', 'employee_id', 'position')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'date_of_birth', 'address', 'phone_number', 'profile_image')
        }),
        ('Employment Details', {
            'fields': ('employee_id', 'position', 'department', 'hire_date', 'end_date', 'is_active')
        }),
        ('Salary & Payment', {
            'fields': ('base_salary', 'bank_account', 'bank_name')
        }),
        ('Additional Information', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Name'
