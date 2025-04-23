from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.utils.translation import gettext_lazy as _

class UserRole(models.Model):
    """Model to define user roles with specific permissions"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('permissions'),
        blank=True,
    )
    is_admin_role = models.BooleanField(default=False, 
                                       help_text=_('Designates whether this role has admin privileges'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('user role')
        verbose_name_plural = _('user roles')
        ordering = ['name']

class UserProfile(models.Model):
    """Extended profile for users with role assignment"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(UserRole, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"
    
    @property
    def is_admin(self):
        """Check if user has admin role"""
        return self.role and self.role.is_admin_role
