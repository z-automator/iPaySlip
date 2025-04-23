from django import forms
from django.contrib.auth.models import User, Permission
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.db.models import Q
from .models import UserRole, UserProfile

class UserRoleForm(forms.ModelForm):
    """Form for creating and editing user roles"""
    
    class Meta:
        model = UserRole
        fields = ['name', 'description', 'permissions', 'is_admin_role']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'permissions': forms.CheckboxSelectMultiple(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter permissions to show only relevant ones for the payslip application
        self.fields['permissions'].queryset = Permission.objects.exclude(
            Q(content_type__app_label='admin') | 
            Q(content_type__app_label='contenttypes') |
            Q(content_type__app_label='sessions') |
            Q(content_type__app_label='auth', name__contains='group')
        ).order_by('content_type__app_label', 'name')
        
        # Add help text to explain permissions
        self.fields['permissions'].help_text = "Select the permissions for this role"

class CustomUserCreationForm(UserCreationForm):
    """Extended user creation form with role selection"""
    role = forms.ModelChoiceField(
        queryset=UserRole.objects.all(),
        required=False,
        help_text="Select a role for this user"
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
    
    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            # Create or update user profile with selected role
            role = self.cleaned_data.get('role')
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    """Extended user edit form with role selection"""
    role = forms.ModelChoiceField(
        queryset=UserRole.objects.all(),
        required=False,
        help_text="Select a role for this user"
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        exclude = ['password']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            try:
                self.fields['role'].initial = self.instance.profile.role
            except UserProfile.DoesNotExist:
                pass
    
    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            # Create or update user profile with selected role
            role = self.cleaned_data.get('role')
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()
        return user
