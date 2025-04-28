from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.http import Http404, HttpResponseForbidden
from employees.models import Employee

class ManagerRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only managers can access the view"""
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return HttpResponseForbidden("You don't have permission to access this page.")

class EmployeeAccessMixin(UserPassesTestMixin):
    """Mixin to ensure users can only access their own employee data"""
    def test_func(self):
        # Check if the user is authenticated
        if not self.request.user.is_authenticated:
            return False
            
        # Managers can access all employee data
        if self.request.user.is_superuser:
            return True
            
        # For ListView, we'll filter in get_queryset
        if self.request.resolver_match.func.__name__ == 'EmployeeListView':
            return True
            
        # For DetailView, check if the employee belongs to the user
        if hasattr(self, 'get_object'):
            try:
                obj = super().get_object()
                return obj.user == self.request.user
            except:
                pass
                
        # For other views, check if user has an employee profile
        try:
            self.employee = Employee.objects.get(user=self.request.user)
            return True
        except Employee.DoesNotExist:
            return False
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this resource.")
        return HttpResponseForbidden("You don't have permission to access this resource.")
