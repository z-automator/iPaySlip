from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from employees.models import Employee
from payroll.models import Payroll
from lending.models import Loan
from leaves.models import Leave
from lending.forms import LoanForm
from django.http import HttpResponseForbidden

# Mixin to ensure only employees can access their own data
class EmployeeAccessMixin(UserPassesTestMixin):
    """Mixin to ensure users can only access their own employee data"""
    
    def test_func(self):
        # Check if the user is authenticated and has an associated employee profile
        if not self.request.user.is_authenticated:
            return False
            
        try:
            # Get the employee associated with the current user
            self.employee = Employee.objects.get(user=self.request.user)
            return True
        except Employee.DoesNotExist:
            return False
    
    def handle_no_permission(self):
        return redirect('home')

@login_required
def employee_dashboard(request):
    """Dashboard view for employee portal"""
    try:
        # Get the employee associated with the current user
        employee = Employee.objects.get(user=request.user)
        
        # Get recent payrolls
        recent_payrolls = Payroll.objects.filter(employee=employee).order_by('-period__payment_date')[:5]
        
        # Get active loans
        active_loans = Loan.objects.filter(employee=employee, status='active').order_by('-request_date')
        
        # Get recent leave requests
        recent_leave_requests = Leave.objects.filter(employee=request.user).order_by('-created_at')[:5]
        
        context = {
            'employee': employee,
            'recent_payrolls': recent_payrolls,
            'active_loans': active_loans,
            'recent_leave_requests': recent_leave_requests,
        }
        
        return render(request, 'employee_portal/dashboard.html', context)
    except Employee.DoesNotExist:
        messages.error(request, "You don't have an employee profile in the system.")
        return redirect('home')

# Payroll Views
class PayrollListView(LoginRequiredMixin, EmployeeAccessMixin, ListView):
    """View for employees to see their payroll history"""
    model = Payroll
    template_name = 'employee_portal/payroll_list.html'
    context_object_name = 'payrolls'
    paginate_by = 10
    
    def get_queryset(self):
        # Filter payrolls for the current employee only
        return Payroll.objects.filter(employee=self.employee).order_by('-period__payment_date')

class PayrollDetailView(LoginRequiredMixin, EmployeeAccessMixin, DetailView):
    """View for employees to see details of a specific payroll"""
    model = Payroll
    template_name = 'employee_portal/payroll_detail.html'
    context_object_name = 'payroll'
    
    def get_object(self, queryset=None):
        # Get the payroll object and ensure it belongs to the current employee
        obj = super().get_object(queryset)
        if obj.employee != self.employee:
            raise HttpResponseForbidden("You don't have permission to view this payroll.")
        return obj

# Loan Views
class LoanListView(LoginRequiredMixin, EmployeeAccessMixin, ListView):
    """View for employees to see their loan history"""
    model = Loan
    template_name = 'employee_portal/loan_list.html'
    context_object_name = 'loans'
    paginate_by = 10
    
    def get_queryset(self):
        # Filter loans for the current employee only
        return Loan.objects.filter(employee=self.employee).order_by('-request_date')

class LoanDetailView(LoginRequiredMixin, EmployeeAccessMixin, DetailView):
    """View for employees to see details of a specific loan"""
    model = Loan
    template_name = 'employee_portal/loan_detail.html'
    context_object_name = 'loan'
    
    def get_object(self, queryset=None):
        # Get the loan object and ensure it belongs to the current employee
        obj = super().get_object(queryset)
        if obj.employee != self.employee:
            raise HttpResponseForbidden("You don't have permission to view this loan.")
        return obj

class LoanRequestView(LoginRequiredMixin, EmployeeAccessMixin, CreateView):
    """View for employees to request a new loan"""
    model = Loan
    form_class = LoanForm
    template_name = 'employee_portal/loan_form.html'
    success_url = reverse_lazy('employee_loan_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # We don't need to pass employee as a kwarg since we'll set it in form_valid
        return kwargs
    
    def form_valid(self, form):
        form.instance.employee = self.employee
        form.instance.status = 'pending'  # Set initial status to pending
        messages.success(self.request, "Loan request submitted successfully. It is pending approval.")
        return super().form_valid(form)

# Leave Request Views
class LeaveRequestListView(LoginRequiredMixin, EmployeeAccessMixin, ListView):
    """View for employees to see their leave request history"""
    model = Leave
    template_name = 'employee_portal/leave_request_list.html'
    context_object_name = 'leave_requests'
    paginate_by = 10
    
    def get_queryset(self):
        # Filter leave requests for the current employee only
        return Leave.objects.filter(employee=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get leave types from the choices field
        context['leave_types'] = [{'name': name, 'description': name} for code, name in Leave.LEAVE_TYPE_CHOICES]
        return context

class LeaveRequestDetailView(LoginRequiredMixin, EmployeeAccessMixin, DetailView):
    """View for employees to see details of a specific leave request"""
    model = Leave
    template_name = 'employee_portal/leave_request_detail.html'
    context_object_name = 'leave_request'
    
    def get_object(self, queryset=None):
        # Get the leave request object and ensure it belongs to the current employee
        obj = super().get_object(queryset)
        if obj.employee != self.request.user:
            raise HttpResponseForbidden("You don't have permission to view this leave request.")
        return obj

class LeaveRequestCreateView(LoginRequiredMixin, EmployeeAccessMixin, CreateView):
    """View for employees to create a new leave request"""
    model = Leave
    template_name = 'employee_portal/leave_request_form.html'
    fields = ['leave_type', 'start_date', 'end_date', 'reason']
    success_url = reverse_lazy('employee_leave_request_list')
    
    def form_valid(self, form):
        form.instance.employee = self.request.user
        form.instance.status = 'pending'  # Set initial status to pending
        messages.success(self.request, "Leave request submitted successfully. It is pending approval.")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Request Leave'
        context['button_label'] = 'Submit Request'
        return context
