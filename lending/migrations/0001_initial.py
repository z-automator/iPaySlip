# Generated by Django 4.2.8 on 2025-03-01 10:55

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Loan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('interest_rate', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('term_months', models.PositiveIntegerField()),
                ('monthly_payment', models.DecimalField(decimal_places=2, max_digits=12)),
                ('total_payable', models.DecimalField(decimal_places=2, max_digits=12)),
                ('status', models.CharField(choices=[('pending', 'Pending Approval'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('active', 'Active'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('request_date', models.DateField(default=django.utils.timezone.now)),
                ('approval_date', models.DateField(blank=True, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('expected_end_date', models.DateField(blank=True, null=True)),
                ('actual_end_date', models.DateField(blank=True, null=True)),
                ('purpose', models.TextField()),
                ('rejection_reason', models.TextField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loans', to='employees.employee')),
            ],
            options={
                'ordering': ['-request_date'],
            },
        ),
        migrations.CreateModel(
            name='LoanType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('interest_rate', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('max_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('max_term_months', models.PositiveIntegerField()),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='LoanPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_date', models.DateField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('is_paid', models.BooleanField(default=False)),
                ('paid_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('payment_source', models.CharField(choices=[('manual', 'Manual Payment'), ('payroll', 'Payroll Deduction')], default='payroll', max_length=20)),
                ('payroll_reference', models.CharField(blank=True, max_length=100)),
                ('loan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='lending.loan')),
            ],
            options={
                'ordering': ['payment_date'],
            },
        ),
        migrations.AddField(
            model_name='loan',
            name='loan_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='loans', to='lending.loantype'),
        ),
    ]
