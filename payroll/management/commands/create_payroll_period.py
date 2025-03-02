from django.core.management.base import BaseCommand
from payroll.models import PayrollPeriod
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Creates a sample PayrollPeriod'

    def handle(self, *args, **options):
        # Create a sample PayrollPeriod for June 2023
        period, created = PayrollPeriod.objects.get_or_create(
            name='June 2023',
            defaults={
                'start_date': datetime.date(2023, 6, 1),
                'end_date': datetime.date(2023, 6, 30),
                'payment_date': datetime.date(2023, 7, 5),
                'is_active': True
            }
        )
        
        # Create a sample PayrollPeriod for July 2023
        period2, created2 = PayrollPeriod.objects.get_or_create(
            name='July 2023',
            defaults={
                'start_date': datetime.date(2023, 7, 1),
                'end_date': datetime.date(2023, 7, 31),
                'payment_date': datetime.date(2023, 8, 5),
                'is_active': True
            }
        )
        
        # Create a sample PayrollPeriod for August 2023
        period3, created3 = PayrollPeriod.objects.get_or_create(
            name='August 2023',
            defaults={
                'start_date': datetime.date(2023, 8, 1),
                'end_date': datetime.date(2023, 8, 31),
                'payment_date': datetime.date(2023, 9, 5),
                'is_active': True
            }
        )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created PayrollPeriods')) 