# Generated by Django 4.2.8 on 2025-03-03 11:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0002_taxtier'),
        ('lending', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='loanpayment',
            name='payment_number',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='loanpayment',
            name='payroll',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='loan_payments', to='payroll.payroll'),
        ),
    ]
