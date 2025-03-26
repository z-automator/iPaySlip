import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payslip.settings')
django.setup()

from django.contrib.auth.models import User

print(f'Found {User.objects.count()} users:')
for user in User.objects.all():
    print(f'  - {user.username} (Admin: {user.is_superuser})') 