from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.contrib import messages

class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom account adapter for django-allauth"""
    
    def get_logout_redirect_url(self, request):
        """Override to redirect to home page after logout"""
        return settings.LOGOUT_REDIRECT_URL
    
    def add_message(self, request, level, message_template, message_context=None, extra_tags=''):
        """Override to customize the logout message"""
        if 'signed out' in message_template.lower():
            # Replace the default logout message with a custom one
            message = "You have successfully logged out."
            messages.add_message(request, level, message, extra_tags=extra_tags)
        else:
            # Use the default behavior for other messages
            super().add_message(request, level, message_template, message_context, extra_tags) 