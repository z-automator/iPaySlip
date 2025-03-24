#!/usr/bin/env python
"""
Script to quickly delete all payslip records from the database.
This will remove all Payroll records and related PayrollEntry records without confirmation.
Use with caution as this action cannot be undone.
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payslip.settings')
django.setup()

# Now import Django models
from payroll.models import Payroll, PayrollEntry
from django.db import transaction

print("Deleting all payslips from the database...")

try:
    with transaction.atomic():
        # Count records before deletion
        payroll_count = Payroll.objects.count()
        entry_count = PayrollEntry.objects.count()
        
        # Delete all payroll entries first (to avoid foreign key constraints)
        PayrollEntry.objects.all().delete()
        
        # Then delete all payrolls
        Payroll.objects.all().delete()
        
        print(f"Successfully deleted {payroll_count} payroll records and {entry_count} payroll entries.")
        
except Exception as e:
    print(f"Error occurred while deleting payslips: {e}") 