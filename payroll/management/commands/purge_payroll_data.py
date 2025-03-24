from django.core.management.base import BaseCommand
from django.db import transaction
from payroll.models import Payroll, PayrollEntry
from lending.models import LoanPayment  # Import related models


class Command(BaseCommand):
    help = 'Purge all payroll records and their related data from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion without confirmation',
        )
        parser.add_argument(
            '--keep-loan-data',
            action='store_true',
            help='Keep loan payment records, just set their payroll reference to null',
        )

    def handle(self, *args, **kwargs):
        force = kwargs.get('force', False)
        keep_loan_data = kwargs.get('keep_loan_data', False)
        
        # Count records before deletion
        payroll_count = Payroll.objects.count()
        entry_count = PayrollEntry.objects.count()
        loan_payment_count = LoanPayment.objects.filter(payroll__isnull=False).count()
        
        if payroll_count == 0:
            self.stdout.write(self.style.WARNING('No payroll records found to delete.'))
            return
            
        # Ask for confirmation unless forced
        if not force:
            self.stdout.write(
                self.style.WARNING(f'You are about to delete {payroll_count} payroll records, '
                                  f'{entry_count} payroll entries, and affect {loan_payment_count} loan payments. '
                                  f'This cannot be undone!')
            )
            
            confirm = input("Type 'yes' to confirm: ")
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Operation cancelled.'))
                return
        
        try:
            with transaction.atomic():
                # Handle loan payments first
                if keep_loan_data:
                    # Just clear the references to payroll
                    loan_payments_updated = LoanPayment.objects.filter(payroll__isnull=False).update(payroll=None)
                    self.stdout.write(self.style.SUCCESS(f'Updated {loan_payments_updated} loan payments to remove payroll references.'))
                else:
                    # Delete loan payments associated with payrolls
                    loan_payments_deleted = LoanPayment.objects.filter(payroll__isnull=False).delete()[0]
                    self.stdout.write(self.style.SUCCESS(f'Deleted {loan_payments_deleted} loan payments.'))
                
                # Delete all payroll entries
                PayrollEntry.objects.all().delete()
                
                # Delete all payrolls
                Payroll.objects.all().delete()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully deleted {payroll_count} payroll records and '
                                      f'{entry_count} payroll entries.')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error occurred while purging payroll data: {e}')
            ) 