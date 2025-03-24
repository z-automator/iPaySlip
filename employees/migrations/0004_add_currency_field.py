from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0005_add_currency_fields'),
        ('employees', '0003_employee_hourly_rate_employee_salary_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='salary_currency',
            field=models.ForeignKey(default=1, help_text='Currency for salary/hourly rate', on_delete=django.db.models.deletion.PROTECT, related_name='employees', to='payroll.currency'),
        ),
    ] 