from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User

from .models import Employee, Department
from .forms import EmployeeForm, DepartmentForm

class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
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

class EmployeeDetailView(LoginRequiredMixin, DetailView):
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

class EmployeeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employee_list')
    permission_required = 'employees.add_employee'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Employee'
        context['button_label'] = 'Create Employee'
        return context
    
    def form_valid(self, form):
        try:
            employee = form.save(commit=False)
            
            # Get the user field from the form data or create a new user
            user_id = self.request.POST.get('user')
            first_name = self.request.POST.get('first_name', '')
            last_name = self.request.POST.get('last_name', '')
            email = self.request.POST.get('email', '')
            
            if user_id:
                employee.user = User.objects.get(id=user_id)
                # Update the user's email if it has changed
                if employee.user.email != email:
                    employee.user.email = email
                    employee.user.save()
            else:
                # Create a user based on employee information
                username = email.split('@')[0]
                # Check if username exists, if so append a random string
                if User.objects.filter(username=username).exists():
                    import random, string
                    random_suffix = ''.join(random.choices(string.digits, k=4))
                    username = f"{username}_{random_suffix}"
                
                # Generate a random password
                import random, string
                password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                employee.user = user
                
                # Send email with login credentials
                from django.core.mail import send_mail
                from django.conf import settings
                
                subject = f"Your {settings.COMPANY_NAME} Account Details"
                message = f"""
Hello {first_name} {last_name},

Your account has been created in the {settings.COMPANY_NAME} payroll system.

Username: {username}
Password: {password}

Please login at {settings.COMPANY_WEBSITE}/accounts/login/ and change your password.

Regards,
{settings.COMPANY_NAME} HR Team
                """
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )
                    messages.success(self.request, f"Login credentials have been sent to {email}")
                except Exception as e:
                    messages.warning(self.request, f"Could not send email: {str(e)}")
            
            employee.save()
            messages.success(self.request, "Employee created successfully.")
            return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, f"Error creating employee: {str(e)}")
            return super().form_invalid(form)

class EmployeeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employee_list')
    permission_required = 'employees.change_employee'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Employee'
        context['button_label'] = 'Update Employee'
        return context
    
    def form_valid(self, form):
        try:
            employee = form.save(commit=False)
            
            # Handle user update
            user_id = self.request.POST.get('user')
            first_name = self.request.POST.get('first_name', '')
            last_name = self.request.POST.get('last_name', '')
            email = self.request.POST.get('email', '')
            
            if user_id:
                # Link to selected user
                employee.user = User.objects.get(id=user_id)
                # Update the user's email if it has changed
                if employee.user.email != email:
                    employee.user.email = email
                    employee.user.save()
            elif employee.user:
                # Update existing user's name and email
                employee.user.first_name = first_name
                employee.user.last_name = last_name
                if employee.user.email != email:
                    employee.user.email = email
                employee.user.save()
            else:
                # Create a new user
                username = email.split('@')[0]
                # Check if username exists, if so append a random string
                if User.objects.filter(username=username).exists():
                    import random, string
                    random_suffix = ''.join(random.choices(string.digits, k=4))
                    username = f"{username}_{random_suffix}"
                
                # Generate a random password
                import random, string
                password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                employee.user = user
                
                # Send email with login credentials
                from django.core.mail import send_mail
                from django.conf import settings
                
                subject = f"Your {settings.COMPANY_NAME} Account Details"
                message = f"""
Hello {first_name} {last_name},

Your account has been created in the {settings.COMPANY_NAME} payroll system.

Username: {username}
Password: {password}

Please login at {settings.COMPANY_WEBSITE}/accounts/login/ and change your password.

Regards,
{settings.COMPANY_NAME} HR Team
                """
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )
                    messages.success(self.request, f"Login credentials have been sent to {email}")
                except Exception as e:
                    messages.warning(self.request, f"Could not send email: {str(e)}")
            
            employee.save()
            messages.success(self.request, "Employee updated successfully.")
            return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, f"Error updating employee: {str(e)}")
            return super().form_invalid(form)

class EmployeeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Employee
    template_name = 'employees/employee_confirm_delete.html'
    success_url = reverse_lazy('employee_list')
    context_object_name = 'employee'
    permission_required = 'employees.delete_employee'
    
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

class DepartmentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'employees/department_form.html'
    success_url = reverse_lazy('department_list')
    permission_required = 'employees.add_department'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Department'
        context['button_label'] = 'Create Department'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Department created successfully.")
        return super().form_valid(form)

class DepartmentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'employees/department_form.html'
    success_url = reverse_lazy('department_list')
    permission_required = 'employees.change_department'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Department'
        context['button_label'] = 'Update Department'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Department updated successfully.")
        return super().form_valid(form)

class DepartmentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Department
    template_name = 'employees/department_confirm_delete.html'
    success_url = reverse_lazy('department_list')
    permission_required = 'employees.delete_department'
    
    def post(self, request, *args, **kwargs):
        department = self.get_object()
        if department.employee_set.exists():
            messages.error(request, f"Cannot delete department '{department.name}' as it has employees assigned to it. Please reassign employees first.")
            return redirect('department_detail', pk=department.pk)
        
        messages.success(request, f"Department '{department.name}' deleted successfully.")
        return super().post(request, *args, **kwargs)
