from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.models import User, Permission
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from .models import UserRole, UserProfile
from .forms import UserRoleForm, CustomUserCreationForm, CustomUserChangeForm

# Admin check mixin
class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only admin users can access the view"""
    def test_func(self):
        # Check if user is superuser or has admin role
        if self.request.user.is_superuser:
            return True
        try:
            return self.request.user.profile.is_admin
        except (AttributeError, UserProfile.DoesNotExist):
            return False
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('home')  # Redirect to home page if no permission

# User Role Views
class UserRoleListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = UserRole
    template_name = 'user_management/role_list.html'
    context_object_name = 'roles'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
            
        return queryset

class UserRoleDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = UserRole
    template_name = 'user_management/role_detail.html'
    context_object_name = 'role'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get users with this role
        role = self.get_object()
        context['users'] = User.objects.filter(profile__role=role)
        return context

class UserRoleCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = UserRole
    form_class = UserRoleForm
    template_name = 'user_management/role_form.html'
    success_url = reverse_lazy('role_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Role'
        context['button_label'] = 'Create Role'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Role created successfully.")
        return super().form_valid(form)

class UserRoleUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = UserRole
    form_class = UserRoleForm
    template_name = 'user_management/role_form.html'
    success_url = reverse_lazy('role_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Role'
        context['button_label'] = 'Update Role'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Role updated successfully.")
        return super().form_valid(form)

class UserRoleDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = UserRole
    template_name = 'user_management/role_confirm_delete.html'
    success_url = reverse_lazy('role_list')
    context_object_name = 'role'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Role deleted successfully.")
        return super().delete(request, *args, **kwargs)

# User Management Views
class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'user_management/user_list.html'
    context_object_name = 'users'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) | 
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
            
        role = self.request.GET.get('role', '')
        if role:
            queryset = queryset.filter(profile__role_id=role)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = UserRole.objects.all()
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_role'] = self.request.GET.get('role', '')
        return context

class UserDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = User
    template_name = 'user_management/user_detail.html'
    context_object_name = 'user_obj'  # renamed to avoid conflict with request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Get user's permissions (direct + from role)
        direct_permissions = user.user_permissions.all()
        
        try:
            role_permissions = user.profile.role.permissions.all() if user.profile.role else []
        except (AttributeError, UserProfile.DoesNotExist):
            role_permissions = []
            
        context['direct_permissions'] = direct_permissions
        context['role_permissions'] = role_permissions
        
        return context

class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'user_management/user_form.html'
    success_url = reverse_lazy('user_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New User'
        context['button_label'] = 'Create User'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "User created successfully.")
        return super().form_valid(form)

class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'user_management/user_form.html'
    success_url = reverse_lazy('user_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit User'
        context['button_label'] = 'Update User'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "User updated successfully.")
        return super().form_valid(form)

class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'user_management/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')
    context_object_name = 'user_obj'  # renamed to avoid conflict with request.user
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "User deleted successfully.")
        return super().delete(request, *args, **kwargs)
