import os
import sys
import django

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payslip.settings')
django.setup()

from django.contrib.auth.models import User

# Username of the superuser to update
username = 'myroot'
# New password to set
new_password = 'toor123'

try:
    user = User.objects.get(username=username)
    user.set_password(new_password)
    user.save()
    print(f"Password updated successfully for user '{username}'!")
except User.DoesNotExist:
    print(f"Error: User '{username}' does not exist.")
except Exception as e:
    print(f"Error: {e}")