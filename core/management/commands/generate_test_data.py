import os
import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.utils import timezone
from django.conf import settings

from employees.models import Department, Employee
from payroll.models import PayrollPeriod, StandardPayrollItem, Payroll, PayrollEntry
from lending.models import LoanType, Loan, LoanPayment

class Command(BaseCommand):
    help = 'Generate test data for the payslip system'

    def add_arguments(self, parser):
        parser.add_argument('--employees', type=int, default=10, help='Number of employees to create')
        parser.add_argument('--periods', type=int, default=3, help='Number of payroll periods to create')
        parser.add_argument('--payroll-items', type=int, default=5, help='Number of standard payroll items to create')
        parser.add_argument('--loan-types', type=int, default=3, help='Number of loan types to create')
        parser.add_argument('--loans', type=int, default=5, help='Number of loans to create')
        parser.add_argument('--reset', action='store_true', help='Reset existing data before generating new data')
        
    def handle(self, *args, **options):
        num_employees = options['employees']
        num_periods = options['periods']
        num_payroll_items = options['payroll_items']
        num_loan_types = options['loan_types']
        num_loans = options['loans']
        reset = options['reset']
        
        if reset:
            self.reset_data()
            
        self.stdout.write(self.style.NOTICE('Starting data generation...'))
        
        # Create user groups and permissions
        self.create_user_groups()
        
        # Create departments
        departments = self.create_departments()
        
        # Create employees
        employees = self.create_employees(num_employees, departments)
        
        # Create payroll periods
        periods = self.create_payroll_periods(num_periods)
        
        # Create standard payroll items
        payroll_items = self.create_standard_payroll_items(num_payroll_items)
        
        # Create payrolls
        payrolls = self.create_payrolls(employees, periods, payroll_items)
        
        # Create loan types
        loan_types = self.create_loan_types(num_loan_types)
        
        # Create loans
        loans = self.create_loans(num_loans, employees, loan_types, payrolls)
        
        self.stdout.write(self.style.SUCCESS('Test data generation completed!'))
        
        # Summary
        self.stdout.write(self.style.NOTICE('\nGenerated Data Summary:'))
        self.stdout.write(f'Departments: {len(departments)}')
        self.stdout.write(f'Employees: {len(employees)}')
        self.stdout.write(f'Payroll Periods: {len(periods)}')
        self.stdout.write(f'Standard Payroll Items: {len(payroll_items)}')
        self.stdout.write(f'Payrolls: {len(payrolls)}')
        self.stdout.write(f'Loan Types: {len(loan_types)}')
        self.stdout.write(f'Loans: {len(loans)}')
        
    def reset_data(self):
        """Reset existing data"""
        self.stdout.write(self.style.WARNING('Resetting existing data...'))
        
        # Delete in reverse order to avoid integrity errors
        LoanPayment.objects.all().delete()
        Loan.objects.all().delete()
        LoanType.objects.all().delete()
        PayrollEntry.objects.all().delete()
        Payroll.objects.all().delete()
        StandardPayrollItem.objects.all().delete()
        PayrollPeriod.objects.all().delete()
        Employee.objects.all().delete()
        Department.objects.all().delete()
        
        # Reset users except superuser
        User.objects.filter(is_superuser=False).delete()
        
        self.stdout.write(self.style.SUCCESS('Data reset completed'))
        
    def create_user_groups(self):
        """Create user groups and permissions"""
        self.stdout.write('Creating user groups...')
        
        # Create HR group
        hr_group, created = Group.objects.get_or_create(name='HR')
        if created:
            # Add permissions for employee management
            employee_permissions = Permission.objects.filter(
                content_type__app_label='employees',
                content_type__model__in=['employee', 'department']
            )
            hr_group.permissions.add(*employee_permissions)
            
        # Create Payroll Admin group
        payroll_group, created = Group.objects.get_or_create(name='Payroll Admin')
        if created:
            # Add permissions for payroll management
            payroll_permissions = Permission.objects.filter(
                content_type__app_label='payroll',
                content_type__model__in=['payroll', 'payrollperiod', 'standardpayrollitem', 'payrollentry']
            )
            payroll_group.permissions.add(*payroll_permissions)
            
        # Create Finance group
        finance_group, created = Group.objects.get_or_create(name='Finance')
        if created:
            # Add permissions for loan management
            loan_permissions = Permission.objects.filter(
                content_type__app_label='lending',
                content_type__model__in=['loan', 'loantype', 'loanpayment']
            )
            finance_group.permissions.add(*loan_permissions)
            
        # Create Employee group (for self-service)
        employee_group, created = Group.objects.get_or_create(name='Employee')
        
        return [hr_group, payroll_group, finance_group, employee_group]
        
    def create_departments(self):
        """Create basic departments"""
        self.stdout.write('Creating departments...')
        
        departments = []
        department_data = [
            {'name': 'Management', 'description': 'Executive and management team'},
            {'name': 'Human Resources', 'description': 'HR and personnel management'},
            {'name': 'Finance', 'description': 'Finance and accounting'},
            {'name': 'IT', 'description': 'Information technology'},
            {'name': 'Sales', 'description': 'Sales and marketing'},
            {'name': 'Operations', 'description': 'Day-to-day operations'},
            {'name': 'Customer Support', 'description': 'Customer service and support'},
        ]
        
        for data in department_data:
            dept, created = Department.objects.get_or_create(**data)
            departments.append(dept)
            action = 'Created' if created else 'Using existing'
            self.stdout.write(f"{action} department: {dept.name}")
            
        return departments
        
    def create_employees(self, num_employees, departments):
        """Create test employees"""
        self.stdout.write(f'Creating {num_employees} employees...')
        
        employees = []
        first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Jennifer', 'William', 'Elizabeth',
                      'James', 'Patricia', 'Mary', 'Richard', 'Linda', 'Thomas', 'Susan', 'Daniel', 'Jessica', 'Christopher']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Miller', 'Davis', 'Garcia', 'Rodriguez', 'Wilson',
                     'Martinez', 'Anderson', 'Taylor', 'Thomas', 'Hernandez', 'Moore', 'Martin', 'Jackson', 'Thompson', 'White']
        
        # Position for each department
        positions_by_dept = {
            'Management': ['CEO', 'COO', 'CFO', 'CTO', 'Director'],
            'Human Resources': ['HR Manager', 'HR Specialist', 'Recruiter', 'Talent Acquisition'],
            'Finance': ['Finance Manager', 'Accountant', 'Payroll Specialist', 'Financial Analyst'],
            'IT': ['IT Manager', 'Developer', 'System Administrator', 'Network Engineer', 'Database Administrator'],
            'Sales': ['Sales Manager', 'Sales Representative', 'Business Development', 'Marketing Specialist'],
            'Operations': ['Operations Manager', 'Production Supervisor', 'Quality Control', 'Logistics Coordinator'],
            'Customer Support': ['Support Manager', 'Customer Service Representative', 'Technical Support', 'Help Desk']
        }
        
        # Status options with weights
        status_options = ['active'] * 8 + ['inactive'] * 1 + ['on_leave'] * 1
        
        # Employment types
        employment_types = ['full_time'] * 7 + ['part_time'] * 2 + ['contract'] * 1
        
        # Create employees
        for i in range(num_employees):
            # Pick random name
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            # Random department and position
            department = random.choice(departments)
            position = random.choice(positions_by_dept.get(department.name, ['Employee']))
            
            # Generate fake employee ID
            employee_id = f"EMP{random.randint(1000, 9999)}"
            
            # Other random data
            status = random.choice(status_options)
            employment_type = random.choice(employment_types)
            base_salary = Decimal(random.randint(30000, 120000)) / Decimal(12)  # Monthly salary
            
            # Random dates
            years_ago = random.randint(1, 10)
            hire_date = timezone.now().date() - timedelta(days=365 * years_ago + random.randint(1, 365))
            date_of_birth = hire_date.replace(year=hire_date.year - random.randint(22, 55))
            
            # Create user (optional)
            user = None
            if random.random() < 0.3:  # Only 30% of employees have user accounts
                username = f"{first_name.lower()}.{last_name.lower()}"
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': f"{username}@example.com",
                        'is_staff': False,
                        'is_active': True
                    }
                )
                if created:
                    user.set_password('password123')  # Default password for testing
                    user.save()
                    # Add to employee group
                    employee_group = Group.objects.get(name='Employee')
                    user.groups.add(employee_group)
            
            # Create employee
            employee = Employee.objects.create(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                gender=random.choice(['M', 'F']),
                address=f"{random.randint(1, 999)} Test Street, Test City",
                phone=f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                employee_id=employee_id,
                position=position,
                department=department,
                hire_date=hire_date,
                employment_type=employment_type,
                status=status,
                base_salary=base_salary,
                tax_id=f"TX{random.randint(10000000, 99999999)}",
                bank_account=f"BA{random.randint(1000000000, 9999999999)}",
                user=user
            )
            
            employees.append(employee)
            self.stdout.write(f"Created employee: {employee.employee_id} - {employee.get_full_name()}")
            
        return employees
        
    def create_payroll_periods(self, num_periods):
        """Create test payroll periods"""
        self.stdout.write(f'Creating {num_periods} payroll periods...')
        
        periods = []
        today = timezone.now().date()
        current_month = today.replace(day=1)
        
        for i in range(num_periods):
            # Go back i months
            month = current_month.month - i
            year = current_month.year
            
            # Handle previous year
            while month <= 0:
                month += 12
                year -= 1
                
            # Start of month
            start_date = datetime(year, month, 1).date()
            
            # End of month (28-31 depending on month)
            if month == 12:
                end_date = datetime(year, month, 31).date()
            else:
                end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
            
            # Payment date is typically a few days after month end
            payment_date = end_date + timedelta(days=5)
            
            # Period name
            month_name = start_date.strftime('%B')
            period_name = f"{month_name} {year}"
            
            # Create period
            period, created = PayrollPeriod.objects.get_or_create(
                name=period_name,
                defaults={
                    'start_date': start_date,
                    'end_date': end_date,
                    'payment_date': payment_date,
                    'is_active': (i == 0)  # Only current period is active
                }
            )
            
            periods.append(period)
            action = 'Created' if created else 'Using existing'
            self.stdout.write(f"{action} period: {period.name}")
            
        return periods
        
    def create_standard_payroll_items(self, num_items):
        """Create standard payroll items"""
        self.stdout.write(f'Creating standard payroll items...')
        
        items = []
        
        # Fixed standard items (common across most payroll systems)
        standard_items = [
            {
                'name': 'Basic Salary',
                'description': 'Basic monthly salary',
                'type': 'earning',
                'calculation_method': 'fixed',
                'value': 0,  # Will be employee's base salary
                'is_taxable': True,
                'is_active': True
            },
            {
                'name': 'Income Tax',
                'description': 'Standard income tax deduction',
                'type': 'deduction',
                'calculation_method': 'percentage',
                'value': Decimal('20.00'),  # 20% tax
                'is_taxable': False,
                'is_active': True
            },
            {
                'name': 'Health Insurance',
                'description': 'Health insurance premium',
                'type': 'deduction',
                'calculation_method': 'fixed',
                'value': Decimal('150.00'),  # $150 fixed
                'is_taxable': False,
                'is_active': True
            },
            {
                'name': 'Retirement Fund',
                'description': 'Employee retirement contribution',
                'type': 'deduction',
                'calculation_method': 'percentage',
                'value': Decimal('5.00'),  # 5%
                'is_taxable': False,
                'is_active': True
            }
        ]
        
        # Optional items
        optional_items = [
            {
                'name': 'Performance Bonus',
                'description': 'Monthly performance bonus',
                'type': 'earning',
                'calculation_method': 'percentage',
                'value': Decimal('10.00'),  # 10% of base salary
                'is_taxable': True,
                'is_active': True
            },
            {
                'name': 'Transport Allowance',
                'description': 'Monthly transportation allowance',
                'type': 'earning',
                'calculation_method': 'fixed',
                'value': Decimal('100.00'),  # $100 fixed
                'is_taxable': False,
                'is_active': True
            },
            {
                'name': 'Meal Allowance',
                'description': 'Meal subsidy',
                'type': 'earning',
                'calculation_method': 'fixed',
                'value': Decimal('80.00'),  # $80 fixed
                'is_taxable': False,
                'is_active': True
            },
            {
                'name': 'Overtime',
                'description': 'Overtime payment',
                'type': 'earning',
                'calculation_method': 'percentage',
                'value': Decimal('50.00'),  # 50% of base hourly rate
                'is_taxable': True,
                'is_active': True
            },
            {
                'name': 'Professional Development',
                'description': 'Training and courses allowance',
                'type': 'earning',
                'calculation_method': 'fixed',
                'value': Decimal('200.00'),  # $200 fixed
                'is_taxable': False,
                'is_active': True
            },
            {
                'name': 'Union Dues',
                'description': 'Professional or labor union membership fees',
                'type': 'deduction',
                'calculation_method': 'fixed',
                'value': Decimal('30.00'),  # $30 fixed
                'is_taxable': False,
                'is_active': True
            }
        ]
        
        # Add all standard items
        for item_data in standard_items:
            item, created = StandardPayrollItem.objects.get_or_create(
                name=item_data['name'],
                defaults=item_data
            )
            items.append(item)
            action = 'Created' if created else 'Using existing'
            self.stdout.write(f"{action} payroll item: {item.name}")
        
        # Add some optional items (up to num_items total)
        remaining_slots = max(0, num_items - len(standard_items))
        selected_optionals = random.sample(optional_items, min(remaining_slots, len(optional_items)))
        
        for item_data in selected_optionals:
            item, created = StandardPayrollItem.objects.get_or_create(
                name=item_data['name'],
                defaults=item_data
            )
            items.append(item)
            action = 'Created' if created else 'Using existing'
            self.stdout.write(f"{action} payroll item: {item.name}")
            
        return items
        
    def create_payrolls(self, employees, periods, payroll_items):
        """Create payrolls for employees"""
        self.stdout.write('Creating payrolls...')
        
        payrolls = []
        
        # Find basic salary item and required deductions
        basic_salary_item = next((item for item in payroll_items if item.name == 'Basic Salary'), None)
        income_tax_item = next((item for item in payroll_items if item.name == 'Income Tax'), None)
        health_insurance_item = next((item for item in payroll_items if item.name == 'Health Insurance'), None)
        retirement_item = next((item for item in payroll_items if item.name == 'Retirement Fund'), None)
        
        # Find optional earnings
        optional_earnings = [item for item in payroll_items if item.type == 'earning' and item.name != 'Basic Salary']
        optional_deductions = [item for item in payroll_items if item.type == 'deduction' 
                              and item.name not in ['Income Tax', 'Health Insurance', 'Retirement Fund']]
        
        # Create payrolls for each active employee and period
        active_employees = [emp for emp in employees if emp.status == 'active']
        
        for employee in active_employees:
            for period in periods:
                # Skip if payroll already exists
                if Payroll.objects.filter(employee=employee, period=period).exists():
                    continue
                
                # Create payroll
                payroll = Payroll.objects.create(
                    employee=employee,
                    period=period,
                    gross_salary=employee.base_salary,
                    total_deductions=Decimal('0.00'),
                    net_salary=Decimal('0.00'),
                    status=Payroll.COMPLETED if period != periods[0] else Payroll.PENDING,
                    processed_date=period.payment_date if period != periods[0] else None
                )
                
                # Add basic salary entry
                if basic_salary_item:
                    PayrollEntry.objects.create(
                        payroll=payroll,
                        name=basic_salary_item.name,
                        description=basic_salary_item.description,
                        amount=employee.base_salary,
                        is_deduction=False
                    )
                
                # Add random optional earnings (30% chance for each)
                taxable_earnings = employee.base_salary
                for item in optional_earnings:
                    if random.random() < 0.3:  # 30% chance
                        if item.calculation_method == 'percentage':
                            amount = (employee.base_salary * item.value) / Decimal('100.00')
                        else:
                            amount = item.value
                            
                        PayrollEntry.objects.create(
                            payroll=payroll,
                            name=item.name,
                            description=item.description,
                            amount=amount,
                            is_deduction=False
                        )
                        
                        # Add to gross and taxable earnings
                        payroll.gross_salary += amount
                        if item.is_taxable:
                            taxable_earnings += amount
                
                # Calculate and add deductions
                total_deductions = Decimal('0.00')
                
                # Income tax based on taxable earnings
                if income_tax_item:
                    tax_amount = (taxable_earnings * income_tax_item.value) / Decimal('100.00')
                    PayrollEntry.objects.create(
                        payroll=payroll,
                        name=income_tax_item.name,
                        description=income_tax_item.description,
                        amount=tax_amount,
                        is_deduction=True
                    )
                    total_deductions += tax_amount
                
                # Health insurance (fixed)
                if health_insurance_item:
                    PayrollEntry.objects.create(
                        payroll=payroll,
                        name=health_insurance_item.name,
                        description=health_insurance_item.description,
                        amount=health_insurance_item.value,
                        is_deduction=True
                    )
                    total_deductions += health_insurance_item.value
                
                # Retirement (percentage of gross)
                if retirement_item:
                    retirement_amount = (payroll.gross_salary * retirement_item.value) / Decimal('100.00')
                    PayrollEntry.objects.create(
                        payroll=payroll,
                        name=retirement_item.name,
                        description=retirement_item.description,
                        amount=retirement_amount,
                        is_deduction=True
                    )
                    total_deductions += retirement_amount
                
                # Add random optional deductions (20% chance for each)
                for item in optional_deductions:
                    if random.random() < 0.2:  # 20% chance
                        if item.calculation_method == 'percentage':
                            amount = (payroll.gross_salary * item.value) / Decimal('100.00')
                        else:
                            amount = item.value
                            
                        PayrollEntry.objects.create(
                            payroll=payroll,
                            name=item.name,
                            description=item.description,
                            amount=amount,
                            is_deduction=True
                        )
                        total_deductions += amount
                
                # Update payroll totals
                payroll.total_deductions = total_deductions
                payroll.net_salary = payroll.gross_salary - total_deductions
                payroll.save()
                
                payrolls.append(payroll)
                self.stdout.write(f"Created payroll: {payroll.employee} - {payroll.period.name}")
                
        return payrolls
    
    def create_loan_types(self, num_types):
        """Create loan types"""
        self.stdout.write(f'Creating loan types...')
        
        types = []
        loan_type_data = [
            {
                'name': 'Personal Loan',
                'description': 'General purpose personal loan',
                'interest_rate': Decimal('12.00'),
                'max_amount': Decimal('10000.00'),
                'max_term_months': 24,
                'is_active': True
            },
            {
                'name': 'Emergency Loan',
                'description': 'Short-term emergency cash advance',
                'interest_rate': Decimal('8.00'),
                'max_amount': Decimal('5000.00'),
                'max_term_months': 12,
                'is_active': True
            },
            {
                'name': 'Education Loan',
                'description': 'Loan for education and professional development',
                'interest_rate': Decimal('6.00'),
                'max_amount': Decimal('15000.00'),
                'max_term_months': 36,
                'is_active': True
            },
            {
                'name': 'Housing Loan',
                'description': 'Loan for housing down payment or improvements',
                'interest_rate': Decimal('9.00'),
                'max_amount': Decimal('30000.00'),
                'max_term_months': 60,
                'is_active': True
            },
            {
                'name': 'Interest-Free Advance',
                'description': 'Short-term salary advance with no interest',
                'interest_rate': Decimal('0.00'),
                'max_amount': Decimal('3000.00'),
                'max_term_months': 6,
                'is_active': True
            }
        ]
        
        # Create specified number of loan types
        for i in range(min(num_types, len(loan_type_data))):
            data = loan_type_data[i]
            loan_type, created = LoanType.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            types.append(loan_type)
            action = 'Created' if created else 'Using existing'
            self.stdout.write(f"{action} loan type: {loan_type.name}")
            
        return types
        
    def create_loans(self, num_loans, employees, loan_types, payrolls):
        """Create test loans"""
        self.stdout.write(f'Creating {num_loans} loans...')
        
        loans = []
        
        # Only create loans for employees with payrolls
        employees_with_payrolls = list(set([p.employee for p in payrolls]))
        
        # Ensure we don't try to create more loans than we have eligible employees
        num_loans = min(num_loans, len(employees_with_payrolls))
        
        # Sample random employees
        selected_employees = random.sample(employees_with_payrolls, num_loans)
        
        for employee in selected_employees:
            # Random loan type
            loan_type = random.choice(loan_types)
            
            # Random amount (within limits)
            max_amount = loan_type.max_amount
            amount = Decimal(random.randint(
                int(max_amount * Decimal('0.3')), 
                int(max_amount * Decimal('0.9'))
            ))
            
            # Random term (within limits)
            max_term = loan_type.max_term_months
            term_months = random.randint(3, max_term)
            
            # Use loan type interest rate
            interest_rate = loan_type.interest_rate
            
            # Random status (weighted towards active)
            status_options = [
                Loan.PENDING,
                Loan.APPROVED,
                Loan.ACTIVE,
                Loan.ACTIVE,
                Loan.ACTIVE,
                Loan.COMPLETED
            ]
            status = random.choice(status_options)
            
            # Random dates
            today = timezone.now().date()
            request_date = today - timedelta(days=random.randint(30, 365))
            
            # Create the loan
            loan = Loan(
                employee=employee,
                loan_type=loan_type,
                amount=amount,
                interest_rate=interest_rate,
                term_months=term_months,
                purpose=f"Sample loan for {loan_type.name.lower()} purposes",
                status=Loan.PENDING,  # Start as pending, will be updated in save()
                request_date=request_date
            )
            
            # Calculate monthly payment
            loan.monthly_payment = loan.calculate_monthly_payment()
            
            # Save to trigger status date updates
            loan.save()
            
            # Update status after initial save
            if status != Loan.PENDING:
                loan.status = status
                
                # Set approval date for non-pending loans
                loan.approval_date = request_date + timedelta(days=random.randint(1, 7))
                
                # Set start date for active loans
                if status in [Loan.ACTIVE, Loan.COMPLETED]:
                    loan.start_date = loan.approval_date + timedelta(days=random.randint(1, 7))
                    loan.expected_end_date = loan.start_date.replace(
                        month=loan.start_date.month + term_months
                    )
                
                # Set completion date for completed loans
                if status == Loan.COMPLETED:
                    months_ago = random.randint(1, term_months)
                    loan.actual_end_date = today - timedelta(days=30 * months_ago)
                
                loan.save()
            
            # Create payment schedule
            self.create_loan_payments(loan)
            
            loans.append(loan)
            self.stdout.write(f"Created loan: {loan.employee} - {loan.amount} ({loan.status})")
            
        return loans
    
    def create_loan_payments(self, loan):
        """Create payment schedule for a loan"""
        if loan.status == Loan.PENDING or loan.status == Loan.REJECTED:
            return
            
        if not loan.start_date:
            return
            
        # Start from loan start date
        payment_date = loan.start_date
        
        # Create monthly payments
        for i in range(loan.term_months):
            # Move to next month
            month = payment_date.month + 1
            year = payment_date.year
            
            if month > 12:
                month = 1
                year += 1
                
            payment_date = payment_date.replace(year=year, month=month)
            
            # Determine if payment would be paid (based on loan status and date)
            is_paid = False
            paid_date = None
            
            # For active loans, payments in the past are paid
            if loan.status == Loan.ACTIVE and payment_date <= timezone.now().date():
                is_paid = True
                paid_date = payment_date
                
            # For completed loans, all payments are paid
            elif loan.status == Loan.COMPLETED:
                is_paid = True
                # Paid date is either the actual date or payment date, whichever is earlier
                if loan.actual_end_date and payment_date > loan.actual_end_date:
                    # Last payment was the payoff
                    paid_date = loan.actual_end_date
                else:
                    paid_date = payment_date
            
            # Create the payment record
            payment = LoanPayment.objects.create(
                loan=loan,
                payment_date=payment_date,
                amount=loan.monthly_payment,
                is_paid=is_paid,
                paid_date=paid_date,
                payment_source=random.choice([LoanPayment.MANUAL, LoanPayment.PAYROLL]),
                notes=f"Payment {i+1} of {loan.term_months}"
            )
            
            # Add payroll reference for payroll deductions
            if payment.is_paid and payment.payment_source == LoanPayment.PAYROLL:
                payment.payroll_reference = f"PR-{random.randint(10000, 99999)}"
                payment.save() 