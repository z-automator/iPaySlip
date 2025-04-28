from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import get_user_model
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Q
import random

from .models import Employee, Department
from .forms import EmployeeForm, DepartmentForm
from user_management.mixins import ManagerRequiredMixin, EmployeeAccessMixin

class EmployeeListView(LoginRequiredMixin, EmployeeAccessMixin, ListView):
    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Regular employees can only see themselves
        if not self.request.user.is_superuser:
            queryset = queryset.filter(user=self.request.user)
        
        search_query = self.request.GET.get('search', '')
        
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) | 
                Q(user__last_name__icontains=search_query) |
                Q(employee_id__icontains=search_query) |
                Q(position__icontains=search_query)
            )
            
        department = self.request.GET.get('department', '')
        if department:
            queryset = queryset.filter(department_id=department)
            
        status = self.request.GET.get('status', '')
        if status:
            # Convert string 'True'/'False' to boolean for is_active filtering
            is_active = status.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all()
        # Define status choices based on is_active boolean field
        context['status_choices'] = [
            ('true', 'Active'),
            ('false', 'Inactive')
        ]
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_department'] = self.request.GET.get('department', '')
        context['selected_status'] = self.request.GET.get('status', '')
        return context

class EmployeeDetailView(LoginRequiredMixin, EmployeeAccessMixin, DetailView):
    model = Employee
    template_name = 'employees/employee_detail.html'
    context_object_name = 'employee'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_object()
        
        # Get related payrolls and loans
        context['payrolls'] = employee.payrolls.all().order_by('-period__payment_date')[:5]
        context['loans'] = employee.loans.all().order_by('-request_date')[:5]
        
        return context

class EmployeeCreateView(LoginRequiredMixin, ManagerRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employee_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Employee'
        context['button_label'] = 'Create Employee'
        return context
    
    def form_valid(self, form):
        try:
            # Get form data
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            email = form.cleaned_data.get('email')
            user_link = form.cleaned_data.get('user')
            is_active = form.cleaned_data.get('is_active', True)
            
            # If linking to existing user, use that user
            if user_link:
                user = user_link
                # Update the user's name if it has changed
                if user.first_name != first_name or user.last_name != last_name:
                    user.first_name = first_name
                    user.last_name = last_name
                    user.save()
            else:
                # Create a new user account with the provided email
                username = email  # Use email as username
                # Generate a random password
                password = ''.join([random.choice('abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(12)])
                
                # Create the user
                user = get_user_model().objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
            
            # Set the user on the employee instance
            employee = form.save(commit=False)
            employee.user = user
            employee.is_active = is_active
            employee.save()
            
            messages.success(self.request, f"Employee {employee} created successfully.")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error creating employee: {str(e)}")
            form.add_error(None, f"Error creating employee: {str(e)}")
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        # Log all form errors for debugging
        for field, errors in form.errors.items():
            for error in errors:
                field_name = field if field != '__all__' else 'General'
                messages.error(self.request, f"{field_name} error: {error}")
                
            # Add is-invalid class to fields with errors
            if field != '__all__' and field in form.fields:
                css_class = form.fields[field].widget.attrs.get('class', '')
                if 'is-invalid' not in css_class:
                    form.fields[field].widget.attrs['class'] = f"{css_class} is-invalid"
        
        return super().form_invalid(form)

class EmployeeUpdateView(LoginRequiredMixin, ManagerRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employee_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Employee'
        context['button_label'] = 'Update Employee'
        return context
    
    def form_valid(self, form):
        try:
            # Get form data
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            email = form.cleaned_data.get('email')
            user_link = form.cleaned_data.get('user')
            is_active = form.cleaned_data.get('is_active', True)
            
            employee = form.save(commit=False)
            
            # If linking to existing user, use that user
            if user_link:
                # Check if this is a change in linked user
                if employee.user != user_link:
                    employee.user = user_link
                
                # Update the user's name if it has changed
                if user_link.first_name != first_name or user_link.last_name != last_name:
                    user_link.first_name = first_name
                    user_link.last_name = last_name
                    user_link.save()
            elif not employee.user:
                # Create a new user account with the provided email
                username = email  # Use email as username
                # Generate a random password
                password = ''.join([random.choice('abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(12)])
                
                # Create the user
                user = get_user_model().objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                employee.user = user
            else:
                # Update existing user
                employee.user.first_name = first_name
                employee.user.last_name = last_name
                if email:
                    employee.user.email = email
                employee.user.save()
            
            employee.is_active = is_active
            employee.save()
            
            messages.success(self.request, f"Employee {employee} updated successfully.")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error updating employee: {str(e)}")
            form.add_error(None, f"Error updating employee: {str(e)}")
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        # Log all form errors for debugging
        for field, errors in form.errors.items():
            for error in errors:
                field_name = field if field != '__all__' else 'General'
                messages.error(self.request, f"{field_name} error: {error}")
                
            # Add is-invalid class to fields with errors
            if field != '__all__' and field in form.fields:
                css_class = form.fields[field].widget.attrs.get('class', '')
                if 'is-invalid' not in css_class:
                    form.fields[field].widget.attrs['class'] = f"{css_class} is-invalid"
        
        return super().form_invalid(form)

class EmployeeDeleteView(LoginRequiredMixin, ManagerRequiredMixin, DeleteView):
    model = Employee
    template_name = 'employees/employee_confirm_delete.html'
    success_url = reverse_lazy('employee_list')
    context_object_name = 'employee'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Employee deleted successfully.")
        return super().delete(request, *args, **kwargs)

# Department Views
class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = 'employees/department_list.html'
    context_object_name = 'departments'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context

class DepartmentDetailView(LoginRequiredMixin, DetailView):
    model = Department
    template_name = 'employees/department_detail.html'
    context_object_name = 'department'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        department = self.get_object()
        department_employees = Employee.objects.filter(department=department)
        context['department_employees'] = department_employees
        context['active_employees_count'] = department_employees.filter(is_active=True).count()
        return context

class DepartmentCreateView(LoginRequiredMixin, ManagerRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'employees/department_form.html'
    success_url = reverse_lazy('department_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Department'
        context['button_label'] = 'Create Department'
        return context
    
    def form_valid(self, form):
        try:
            department = form.save()
            messages.success(self.request, "Department created successfully.")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error creating department: {str(e)}")
            # Add the error to the form for better visibility
            form.add_error(None, f"Error creating department: {str(e)}")
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        # Log all form errors for debugging
        for field, errors in form.errors.items():
            for error in errors:
                field_name = field if field != '__all__' else 'General'
                messages.error(self.request, f"{field_name} error: {error}")
                
            # Add is-invalid class to fields with errors
            if field != '__all__' and field in form.fields:
                css_class = form.fields[field].widget.attrs.get('class', '')
                if 'is-invalid' not in css_class:
                    form.fields[field].widget.attrs['class'] = f"{css_class} is-invalid"
        
        return super().form_invalid(form)

class DepartmentUpdateView(LoginRequiredMixin, ManagerRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'employees/department_form.html'
    success_url = reverse_lazy('department_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Department'
        context['button_label'] = 'Update Department'
        return context
    
    def form_valid(self, form):
        try:
            department = form.save()
            messages.success(self.request, "Department updated successfully.")
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f"Error updating department: {str(e)}")
            # Add the error to the form for better visibility
            form.add_error(None, f"Error updating department: {str(e)}")
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        # Log all form errors for debugging
        for field, errors in form.errors.items():
            for error in errors:
                field_name = field if field != '__all__' else 'General'
                messages.error(self.request, f"{field_name} error: {error}")
                
            # Add is-invalid class to fields with errors
            if field != '__all__' and field in form.fields:
                css_class = form.fields[field].widget.attrs.get('class', '')
                if 'is-invalid' not in css_class:
                    form.fields[field].widget.attrs['class'] = f"{css_class} is-invalid"
        
        return super().form_invalid(form)

class DepartmentDeleteView(LoginRequiredMixin, ManagerRequiredMixin, DeleteView):
    model = Department
    template_name = 'employees/department_confirm_delete.html'
    success_url = reverse_lazy('department_list')
    
    def post(self, request, *args, **kwargs):
        department = self.get_object()
        if department.employee_set.exists():
            messages.error(request, f"Cannot delete department '{department.name}' as it has employees assigned to it. Please reassign employees first.")
            return redirect('department_detail', pk=department.pk)
        
        messages.success(request, f"Department '{department.name}' deleted successfully.")
        return super().post(request, *args, **kwargs)
