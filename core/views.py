from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from employees.models import Employee
from payroll.models import Payroll, PayrollPeriod
from lending.models import Loan

# Create your views here.

def home_view(request):
    """Home page view"""
    return render(request, 'core/home.html', {
        'title': 'Payslip System'
    })

@login_required
def dashboard_view(request):
    """Dashboard view with statistics"""
    try:
        # Get statistics for dashboard
        employee_count = Employee.objects.count()
        payroll_count = Payroll.objects.count()
        active_loans = Loan.objects.filter(status='active').count()
        
        # Get pending approvals (payrolls that are pending)
        pending_approvals = Payroll.objects.filter(status='pending').count()
        
        # Get recent activities (could be recent payrolls, loans, etc.)
        recent_payrolls = Payroll.objects.order_by('-created_at')[:5]
        recent_loans = Loan.objects.order_by('-created_at')[:5]
        
        # Combine and sort recent activities
        recent_activities = []
        
        for payroll in recent_payrolls:
            recent_activities.append({
                'date': payroll.created_at,
                'description': f'Payroll processed for {payroll.period.name}',
                'status': 'completed' if payroll.status == 'completed' else 'pending',
                'amount': payroll.net_salary
            })
        
        for loan in recent_loans:
            # Get employee name safely
            employee_name = str(loan.employee)
            recent_activities.append({
                'date': loan.created_at,
                'description': f'Loan issued to {employee_name}',
                'status': 'completed' if loan.status in ['approved', 'active'] else 'pending',
                'amount': loan.amount
            })
        
        # Sort by date (newest first)
        recent_activities.sort(key=lambda x: x['date'], reverse=True)
        recent_activities = recent_activities[:5]  # Limit to 5 most recent
        
        context = {
            'title': 'Dashboard',
            'employee_count': employee_count,
            'payroll_count': payroll_count,
            'active_loans': active_loans,
            'pending_approvals': pending_approvals,
            'recent_activities': recent_activities,
        }
        
        return render(request, 'core/dashboard.html', context)
    except Exception as e:
        # For debugging
        import traceback
        context = {
            'title': 'Dashboard Error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        return render(request, 'core/dashboard.html', context)
