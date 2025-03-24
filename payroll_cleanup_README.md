# Payroll Data Cleanup Scripts

This directory contains scripts to manage and clean up payroll data in the SQLite database.

## Options for Deleting Payroll Data

### 1. Django Management Command (Recommended)

The Django management command is the most flexible and safest way to delete payroll data:

```bash
# Show warning and confirmation prompt
python manage.py delete_all_payslips

# Force deletion without confirmation
python manage.py delete_all_payslips --force
```

For more comprehensive cleanup that also handles related data:

```bash
# Delete payroll data and related loan payments
python manage.py purge_payroll_data

# Delete payroll data but keep loan payment records (set payroll=null)
python manage.py purge_payroll_data --keep-loan-data

# Force deletion without confirmation
python manage.py purge_payroll_data --force
```

### 2. Standalone Python Script

A standalone script that requires manual confirmation:

```bash
python delete_payslips.py
```

### 3. Quick Cleanup Script

A script that performs deletion without confirmation (use with caution):

```bash
python clear_payslips.py
```

## Notes

- All deletion operations use database transactions to ensure data consistency
- Always make a backup of your database before performing mass deletions
- These scripts will not delete employee data, only payroll records
- The Django management commands are the most maintainable option as they integrate with Django's ecosystem 