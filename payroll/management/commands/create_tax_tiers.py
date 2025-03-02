from django.core.management.base import BaseCommand
from payroll.models import TaxTier
from decimal import Decimal

class Command(BaseCommand):
    help = 'Creates sample tax tiers for income tax calculation'

    def handle(self, *args, **options):
        # Clear existing tax tiers if needed
        # TaxTier.objects.all().delete()
        
        # Create sample tax tiers
        tiers = [
            {
                'name': 'Tax Free Allowance',
                'min_income': Decimal('0.00'),
                'max_income': Decimal('12500.00'),
                'rate': Decimal('0.00'),
                'is_active': True
            },
            {
                'name': 'Basic Rate',
                'min_income': Decimal('12500.00'),
                'max_income': Decimal('50000.00'),
                'rate': Decimal('20.00'),
                'is_active': True
            },
            {
                'name': 'Higher Rate',
                'min_income': Decimal('50000.00'),
                'max_income': Decimal('150000.00'),
                'rate': Decimal('40.00'),
                'is_active': True
            },
            {
                'name': 'Additional Rate',
                'min_income': Decimal('150000.00'),
                'max_income': Decimal('0.00'),  # No upper limit
                'rate': Decimal('45.00'),
                'is_active': True
            }
        ]
        
        created_count = 0
        for tier_data in tiers:
            # Check if a tier with this name already exists
            if not TaxTier.objects.filter(name=tier_data['name']).exists():
                TaxTier.objects.create(**tier_data)
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created tax tier: {tier_data['name']}"))
            else:
                self.stdout.write(self.style.WARNING(f"Tax tier already exists: {tier_data['name']}"))
        
        self.stdout.write(self.style.SUCCESS(f"Successfully created {created_count} tax tiers")) 