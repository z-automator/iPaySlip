from django.db import migrations, models
from decimal import Decimal

def create_base_currency(apps, schema_editor):
    Currency = apps.get_model('payroll', 'Currency')
    
    # Create EGP as base currency
    Currency.objects.create(
        code='EGP',
        name='Egyptian Pound',
        symbol='£',
        exchange_rate_to_egp=Decimal('1.0000'),
        is_base_currency=True
    )
    
    # Create some common currencies
    Currency.objects.create(
        code='USD',
        name='US Dollar',
        symbol='$',
        exchange_rate_to_egp=Decimal('30.9000')
    )
    
    Currency.objects.create(
        code='EUR',
        name='Euro',
        symbol='€',
        exchange_rate_to_egp=Decimal('33.7000')
    )

class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0003_employeepayrolltemplate_employeepayrolltemplateentry'),
    ]

    operations = [
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='Currency code (e.g., USD, EUR)', max_length=3, unique=True)),
                ('name', models.CharField(help_text='Currency name (e.g., US Dollar)', max_length=50)),
                ('symbol', models.CharField(help_text='Currency symbol (e.g., $)', max_length=5)),
                ('exchange_rate_to_egp', models.DecimalField(decimal_places=4, help_text='Exchange rate to convert to EGP (e.g., 1 USD = 30.90 EGP)', max_digits=10)),
                ('is_base_currency', models.BooleanField(default=False, help_text='Whether this is the base currency (EGP)')),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Currencies',
                'ordering': ['code'],
            },
        ),
        migrations.RunPython(create_base_currency),
    ] 