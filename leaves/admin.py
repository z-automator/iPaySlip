from django.contrib import admin
from .models import Leave

# Register your models here.

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    """Admin interface for Leave model"""
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status', 'created_at')
    list_filter = ('status', 'leave_type', 'start_date')
    search_fields = ('employee__username', 'employee__first_name', 'employee__last_name', 'reason')
    date_hierarchy = 'start_date'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee',)
        }),
        ('Leave Details', {
            'fields': ('leave_type', 'start_date', 'end_date', 'reason')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
