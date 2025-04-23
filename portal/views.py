from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView
from django.db.models import Count, Sum
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta

from employees.models import Employee, Department
from payroll.models import Payroll, PayrollPeriod
from lending.models import Loan
from user_management.models import UserRole, UserProfile

# Helper function to check if user is superuser
def is_superuser(user):
    return user.is_superuser

class SuperuserRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only superusers can access the view"""
    def test_func(self):
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        return redirect('home')  # Redirect to home page if not superuser

@login_required
@user_passes_test(is_superuser)
def portal_dashboard(request):
    """Dashboard view for the admin portal"""
    # Get counts for various models
    employee_count = Employee.objects.count()
    active_employee_count = Employee.objects.filter(is_active=True).count()
    department_count = Department.objects.count()
    
    # Get payroll statistics
    current_date = timezone.now().date()
    # Get first and last day of current month
    first_day = current_date.replace(day=1)
    if current_date.month == 12:
        last_day = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
    
    payroll_this_month = Payroll.objects.filter(
        period__payment_date__gte=first_day,
        period__payment_date__lte=last_day
    )
    
    total_payroll_amount = payroll_this_month.aggregate(
        total=Sum('net_salary')
    )['total'] or 0
    
    # Get loan statistics
    active_loans = Loan.objects.filter(status='active')
    total_loan_amount = active_loans.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Get user statistics
    user_count = UserProfile.objects.count()
    role_count = UserRole.objects.count()
    
    # Get recent activities with correct fields for each model
    recent_employees = Employee.objects.order_by('-hire_date')[:5]
    recent_payrolls = Payroll.objects.order_by('-created_at')[:5]
    recent_loans = Loan.objects.order_by('-request_date')[:5]
    
    context = {
        'employee_count': employee_count,
        'active_employee_count': active_employee_count,
        'department_count': department_count,
        'total_payroll_amount': total_payroll_amount,
        'active_loans': active_loans.count(),
        'total_loan_amount': total_loan_amount,
        'user_count': user_count,
        'role_count': role_count,
        'recent_employees': recent_employees,
        'recent_payrolls': recent_payrolls,
        'recent_loans': recent_loans,
    }
    
    return render(request, 'portal/dashboard.html', context)

class PortalBaseView(LoginRequiredMixin, SuperuserRequiredMixin, TemplateView):
    """Base view for all portal pages"""
    pass

# Additional portal views can be added here
