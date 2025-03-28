import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payslip.settings')
django.setup()

from django.contrib.auth.models import User
from django.db.utils import IntegrityError

# Create superuser
try:
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print("Superuser created successfully!")
    else:
        print("Superuser already exists.")
except IntegrityError:
    print("Error: Superuser could not be created.")
except Exception as e:
    print(f"Error: {e}") 