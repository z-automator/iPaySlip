from django.core.management.base import BaseCommand
from django.db import transaction
from payroll.models import Payroll, PayrollEntry


class Command(BaseCommand):
    help = 'Delete all payroll records and their related entries from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion without confirmation',
        )

    def handle(self, *args, **kwargs):
        force = kwargs.get('force', False)
        
        # Count records before deletion
        payroll_count = Payroll.objects.count()
        entry_count = PayrollEntry.objects.count()
        
        if payroll_count == 0:
            self.stdout.write(self.style.WARNING('No payroll records found to delete.'))
            return
            
        # Ask for confirmation unless forced
        if not force:
            self.stdout.write(
                self.style.WARNING(f'You are about to delete {payroll_count} payroll records and '
                                  f'{entry_count} payroll entries. This cannot be undone!')
            )
            
            confirm = input("Type 'yes' to confirm: ")
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Operation cancelled.'))
                return
        
        try:
            with transaction.atomic():
                # Delete all payroll entries first (to avoid foreign key constraints)
                PayrollEntry.objects.all().delete()
                
                # Then delete all payrolls
                Payroll.objects.all().delete()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully deleted {payroll_count} payroll records and '
                                      f'{entry_count} payroll entries.')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error occurred while deleting payslips: {e}')
            ) 