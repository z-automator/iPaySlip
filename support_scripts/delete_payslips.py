#!/usr/bin/env python
"""
Script to delete all payslip records from the database.
This will remove all Payroll records and related PayrollEntry records.
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payslip.settings')
django.setup()

# Now import Django models
from payroll.models import Payroll, PayrollEntry
from django.db import transaction

def delete_all_payslips():
    """Delete all payslips and their related entries from the database."""
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
        return False
    
    return True

if __name__ == "__main__":
    print("This script will delete ALL payroll records and their entries from the database.")
    print("This action CANNOT be undone. Make sure you have a backup if needed.")
    
    # Ask for confirmation
    confirm = input("Type 'YES' to confirm deletion: ")
    
    if confirm == "YES":
        success = delete_all_payslips()
        if success:
            print("All payslips have been deleted from the database.")
        else:
            print("Failed to delete payslips.")
    else:
        print("Operation cancelled.") 