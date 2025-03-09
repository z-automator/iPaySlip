from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings

class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom account adapter for django-allauth"""
    
    def get_logout_redirect_url(self, request):
        """Override to redirect to home page after logout"""
        return settings.LOGOUT_REDIRECT_URL 