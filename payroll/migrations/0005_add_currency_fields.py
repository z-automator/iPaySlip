from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0004_create_currency_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='payroll',
            name='currency',
            field=models.ForeignKey(default=1, help_text="Currency for this payroll's amounts", on_delete=django.db.models.deletion.PROTECT, to='payroll.currency'),
        ),
        migrations.AddField(
            model_name='payroll',
            name='exchange_rate',
            field=models.DecimalField(decimal_places=4, default=1.0, help_text='Exchange rate to EGP at the time of payroll creation', max_digits=10),
        ),
        migrations.AddField(
            model_name='payroll',
            name='gross_salary_egp',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='payroll',
            name='net_salary_egp',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='payroll',
            name='total_deductions_egp',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='payrollentry',
            name='amount_egp',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
    ] 