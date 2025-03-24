from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import HttpResponse, Http404, JsonResponse
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from employees.models import Employee
from .models import PayrollPeriod, StandardPayrollItem, Payroll, PayrollEntry, TaxTier, EmployeePayrollTemplate
from .forms import PayrollPeriodForm, StandardPayrollItemForm, PayrollForm, PayrollEntryForm, PayrollProcessForm, TaxTierForm
from .utils import generate_payslip_pdf, generate_payroll_report, calculate_income_tax

# Simple view to check if PayrollPeriods were created
def check_periods(request):
    periods = PayrollPeriod.objects.all()
    return HttpResponse(f"PayrollPeriods: {list(periods.values('id', 'name', 'start_date', 'end_date', 'payment_date', 'is_active'))}")

class PayrollListView(LoginRequiredMixin, ListView):
    model = Payroll
    template_name = 'payroll/payroll_list.html'
    context_object_name = 'payrolls'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        period = self.request.GET.get('period', '')
        status = self.request.GET.get('status', '')
        
        if search_query:
            queryset = queryset.filter(
                Q(employee__first_name__icontains=search_query) | 
                Q(employee__last_name__icontains=search_query) |
                Q(employee__employee_id__icontains=search_query)
            )
            
        if period:
            try:
                period_id = int(period)
                queryset = queryset.filter(period_id=period_id)
            except (ValueError, TypeError):
                # If period is not a valid integer, ignore the filter
                pass
            
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['periods'] = PayrollPeriod.objects.all().order_by('-start_date')
        context['status_choices'] = Payroll.STATUS_CHOICES
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_period'] = self.request.GET.get('period', '')
        context['selected_status'] = self.request.GET.get('status', '')
        
        # Summary statistics
        payrolls = self.get_queryset()
        context['total_payrolls'] = payrolls.count()
        context['total_gross'] = payrolls.aggregate(total=Sum('gross_salary'))['total'] or 0
        context['total_deductions'] = payrolls.aggregate(total=Sum('total_deductions'))['total'] or 0
        context['total_net'] = payrolls.aggregate(total=Sum('net_salary'))['total'] or 0
        
        return context

class PayrollDetailView(LoginRequiredMixin, DetailView):
    model = Payroll
    template_name = 'payroll/payroll_detail.html'
    context_object_name = 'payroll'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payroll = self.get_object()
        
        # Get entries grouped by type
        context['earnings'] = payroll.entries.filter(is_deduction=False).order_by('name')
        context['deductions'] = payroll.entries.filter(is_deduction=True).order_by('name')
        
        # Get employee loans for reference
        context['active_loans'] = payroll.employee.loans.filter(
            status='active'
        ).order_by('-start_date')
        
        return context

class PayrollCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Payroll
    form_class = PayrollForm
    template_name = 'payroll/payroll_form.html'
    success_url = reverse_lazy('payroll_list')
    permission_required = 'payroll.add_payroll'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Payroll'
        context['button_label'] = 'Create Payroll'
        
        # If employee is preselected, show their template entries
        employee_id = self.request.GET.get('employee')
        if employee_id:
            try:
                employee = Employee.objects.get(pk=employee_id)
                # Get template if exists
                try:
                    template = employee.payroll_template
                    context['template_entries'] = template.get_entries()
                    context['has_template'] = True
                except:
                    context['has_template'] = False
            except Employee.DoesNotExist:
                pass
                
        return context
    
    def form_valid(self, form):
        with transaction.atomic():
            payroll = form.save(commit=False)
            
            # If no gross salary provided, use employee base salary
            if not payroll.gross_salary:
                payroll.gross_salary = payroll.employee.base_salary
                
            # Default net salary if not provided
            if not payroll.net_salary:
                payroll.net_salary = payroll.gross_salary - payroll.total_deductions
                
            payroll.save()
            
            # Check if we should use template entries
            use_template = self.request.POST.get('use_template') == 'on'
            
            if use_template:
                # Try to get template for this employee
                try:
                    template = payroll.employee.payroll_template
                    # Copy template entries to payroll
                    for entry in template.get_entries():
                        PayrollEntry.objects.create(
                            payroll=payroll,
                            name=entry.name,
                            description=entry.description,
                            amount=entry.amount,
                            is_deduction=entry.is_deduction
                        )
                    messages.success(self.request, "Payroll created with template entries.")
                except:
                    # If no template exists, add basic salary entry
                    self._add_basic_salary_entry(payroll)
                    messages.info(self.request, "No template found. Added basic salary entry.")
            else:
                # Add basic salary entry automatically
                self._add_basic_salary_entry(payroll)
                
            # Update payroll totals
            update_payroll_totals(payroll)
                
            messages.success(self.request, "Payroll created successfully.")
            return redirect('payroll_update', pk=payroll.pk)
        
        return super().form_valid(form)
        
    def _add_basic_salary_entry(self, payroll):
        """Add basic salary entry to payroll"""
        PayrollEntry.objects.create(
            payroll=payroll,
            name='Basic Salary',
            description='Monthly base salary',
            amount=payroll.employee.base_salary,
            is_deduction=False
        )

class PayrollUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Payroll
    form_class = PayrollForm
    template_name = 'payroll/payroll_form.html'
    permission_required = 'payroll.change_payroll'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Payroll'
        context['button_label'] = 'Update Payroll'
        
        # Entry management
        context['entry_form'] = PayrollEntryForm(initial={'payroll': self.object})
        context['entries'] = PayrollEntry.objects.filter(payroll=self.object).order_by('-is_deduction', 'name')
        context['earnings'] = PayrollEntry.objects.filter(payroll=self.object, is_deduction=False)
        context['deductions'] = PayrollEntry.objects.filter(payroll=self.object, is_deduction=True)
        
        # Show standard items that can be added
        context['standard_items'] = StandardPayrollItem.objects.filter(is_active=True)
        
        return context
    
    def get_success_url(self):
        return reverse('payroll_detail', args=[self.object.pk])
    
    def form_valid(self, form):
        with transaction.atomic():
            payroll = form.save()
            
            # Update payroll totals
            update_payroll_totals(payroll)
            
            # If payroll is completed, update the employee's template
            if payroll.status == Payroll.COMPLETED:
                template = EmployeePayrollTemplate.get_or_create_for_employee(payroll.employee)
                template.update_from_payroll(payroll)
                messages.info(self.request, "Employee payroll template updated for future use.")
            
            messages.success(self.request, "Payroll updated successfully.")
            
        return super().form_valid(form)

class PayrollDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Payroll
    template_name = 'payroll/payroll_confirm_delete.html'
    success_url = reverse_lazy('payroll_list')
    permission_required = 'payroll.delete_payroll'
    context_object_name = 'payroll'
    
    def delete(self, request, *args, **kwargs):
        payroll = self.get_object()
        
        # Don't allow deleting completed payrolls
        if payroll.status == Payroll.COMPLETED:
            messages.error(request, "Cannot delete a completed payroll.")
            return redirect('payroll_detail', pk=payroll.pk)
            
        # Delete associated entries
        PayrollEntry.objects.filter(payroll=payroll).delete()
        
        messages.success(request, "Payroll deleted successfully.")
        return super().delete(request, *args, **kwargs)

@login_required
@permission_required('payroll.view_payroll')
def generate_payslip_pdf_view(request, pk):
    try:
        payroll = Payroll.objects.get(pk=pk)
        return generate_payslip_pdf(payroll)
    except Payroll.DoesNotExist:
        raise Http404("Payroll not found")

@login_required
@permission_required('payroll.add_payrollentry')
def add_payroll_entry(request, pk):
    """Add or update a payroll entry"""
    payroll = get_object_or_404(Payroll, pk=pk)
    
    if request.method == 'POST':
        entry_id = request.POST.get('entry_id')
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        amount = request.POST.get('amount')
        is_deduction = request.POST.get('is_deduction') == 'on'
        
        try:
            with transaction.atomic():
                if entry_id:  # Update existing entry
                    entry = get_object_or_404(PayrollEntry, pk=entry_id, payroll=payroll)
                    entry.name = name
                    entry.description = description
                    entry.amount = amount
                    entry.is_deduction = is_deduction
                    entry.save()
                    messages.success(request, "Entry updated successfully.")
                else:  # Create new entry
                    PayrollEntry.objects.create(
                        payroll=payroll,
                        name=name,
                        description=description,
                        amount=amount,
                        is_deduction=is_deduction
                    )
                    messages.success(request, "Entry added successfully.")
                
                # Update payroll totals
                update_payroll_totals(payroll)
                
        except Exception as e:
            messages.error(request, f"Error saving entry: {str(e)}")
    
    return redirect('payroll_update', pk=payroll.pk)

@login_required
@permission_required('payroll.delete_payrollentry')
def delete_payroll_entry(request, pk):
    """Delete a payroll entry"""
    entry = get_object_or_404(PayrollEntry, pk=pk)
    payroll = entry.payroll
    
    try:
        with transaction.atomic():
            entry.delete()
            messages.success(request, "Entry deleted successfully.")
            
            # Update payroll totals
            update_payroll_totals(payroll)
            
    except Exception as e:
        messages.error(request, f"Error deleting entry: {str(e)}")
    
    return redirect('payroll_update', pk=payroll.pk)

def update_payroll_totals(payroll):
    """Update payroll totals based on entries"""
    # Calculate totals in original currency
    earnings_sum = payroll.entries.filter(is_deduction=False).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    deductions_sum = payroll.entries.filter(is_deduction=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Update original currency amounts
    payroll.gross_salary = earnings_sum
    payroll.total_deductions = deductions_sum
    payroll.net_salary = earnings_sum - deductions_sum
    
    # Calculate totals in EGP
    earnings_sum_egp = payroll.entries.filter(is_deduction=False).aggregate(total=Sum('amount_egp'))['total'] or Decimal('0.00')
    deductions_sum_egp = payroll.entries.filter(is_deduction=True).aggregate(total=Sum('amount_egp'))['total'] or Decimal('0.00')
    
    # Update EGP amounts
    payroll.gross_salary_egp = earnings_sum_egp
    payroll.total_deductions_egp = deductions_sum_egp
    payroll.net_salary_egp = earnings_sum_egp - deductions_sum_egp
    
    payroll.save()
    
    return payroll

# Payroll Period Views
class PayrollPeriodListView(LoginRequiredMixin, ListView):
    model = PayrollPeriod
    template_name = 'payroll/period_list.html'
    context_object_name = 'periods'
    paginate_by = 10
    
    def get_queryset(self):
        return PayrollPeriod.objects.all().order_by('-start_date')

class PayrollPeriodCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = PayrollPeriod
    form_class = PayrollPeriodForm
    template_name = 'payroll/period_form.html'
    success_url = reverse_lazy('period_list')
    permission_required = 'payroll.add_payrollperiod'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Payroll Period'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Payroll period created successfully.")
        return super().form_valid(form)

class PayrollPeriodUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = PayrollPeriod
    form_class = PayrollPeriodForm
    template_name = 'payroll/period_form.html'
    success_url = reverse_lazy('period_list')
    permission_required = 'payroll.change_payrollperiod'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Payroll Period'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Payroll period updated successfully.")
        return super().form_valid(form)

class PayrollPeriodDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = PayrollPeriod
    template_name = 'payroll/period_confirm_delete.html'
    success_url = reverse_lazy('period_list')
    permission_required = 'payroll.delete_payrollperiod'
    
    def delete(self, request, *args, **kwargs):
        period = self.get_object()
        
        # Check if period has associated payrolls
        if Payroll.objects.filter(period=period).exists():
            messages.error(request, "Cannot delete period with associated payrolls.")
            return redirect('period_list')
            
        messages.success(request, "Payroll period deleted successfully.")
        return super().delete(request, *args, **kwargs)

# Payroll Item Views
class PayrollItemListView(LoginRequiredMixin, ListView):
    model = StandardPayrollItem
    template_name = 'payroll/item_list.html'
    context_object_name = 'items'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by type if provided
        item_type = self.request.GET.get('type', '')
        if item_type:
            queryset = queryset.filter(type=item_type)
            
        # Filter by active status
        show_inactive = self.request.GET.get('show_inactive', False)
        if not show_inactive:
            queryset = queryset.filter(is_active=True)
            
        return queryset.order_by('type', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type_choices'] = StandardPayrollItem.ITEM_TYPE_CHOICES
        context['selected_type'] = self.request.GET.get('type', '')
        context['show_inactive'] = self.request.GET.get('show_inactive', False)
        return context

class PayrollItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = StandardPayrollItem
    form_class = StandardPayrollItemForm
    template_name = 'payroll/item_form.html'
    success_url = reverse_lazy('item_list')
    permission_required = 'payroll.add_standardpayrollitem'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Payroll Item'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Payroll item created successfully.")
        return super().form_valid(form)

class PayrollItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = StandardPayrollItem
    form_class = StandardPayrollItemForm
    template_name = 'payroll/item_form.html'
    success_url = reverse_lazy('item_list')
    permission_required = 'payroll.change_standardpayrollitem'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Payroll Item'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Payroll item updated successfully.")
        return super().form_valid(form)

class PayrollItemDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = StandardPayrollItem
    template_name = 'payroll/item_confirm_delete.html'
    success_url = reverse_lazy('item_list')
    permission_required = 'payroll.delete_standardpayrollitem'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Payroll item deleted successfully.")
        return super().delete(request, *args, **kwargs)

class PayrollProcessView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = 'payroll/process_payroll.html'
    form_class = PayrollProcessForm
    success_url = reverse_lazy('payroll_list')
    permission_required = 'payroll.add_payroll'
    
    def form_valid(self, form):
        period = form.cleaned_data['period']
        include_all_active = form.cleaned_data['include_all_active_employees']
        
        # Get employees to process
        if include_all_active:
            employees = Employee.objects.filter(is_active=True)
        else:
            # In a real application, you might have selected employees from a list
            employees = []
            
        payrolls_created = self.process_payroll(employees, period)
        
        messages.success(self.request, f"Processed payroll for {payrolls_created} employees.")
        return super().form_valid(form)
    
    def process_payroll(self, employees, period):
        """Process payroll for the given employees and period"""
        payrolls_created = []
        
        for employee in employees:
            # Check if payroll already exists for this employee and period
            if Payroll.objects.filter(employee=employee, period=period).exists():
                messages.warning(self.request, f"Payroll already exists for {employee.full_name} in {period.name}")
                continue
            
            # Calculate gross salary based on salary type
            if employee.salary_type == 'monthly':
                gross_salary = employee.base_salary
            else:  # hourly rate
                # Calculate total hours for the period (assuming standard 8 hours/day, 22 days/month)
                standard_hours = 8 * 22  # 176 hours per month
                gross_salary = employee.hourly_rate * standard_hours
            
            # Create new payroll
            payroll = Payroll.objects.create(
                employee=employee,
                period=period,
                gross_salary=gross_salary,
                status=Payroll.PENDING
            )
            
            # Check if employee has a payroll template
            has_template = False
            try:
                if hasattr(employee, 'payroll_template'):
                    template = employee.payroll_template
                    has_template = True
                    # Use template entries
                    for entry in template.get_entries():
                        PayrollEntry.objects.create(
                            payroll=payroll,
                            name=entry.name,
                            description=entry.description,
                            amount=entry.amount,
                            is_deduction=entry.is_deduction
                        )
                    # Add loan repayments that might not be in the template
                    self._add_loan_repayments(payroll, employee)
            except Exception as e:
                # Log the error
                print(f"Error processing template for employee {employee.id}: {str(e)}")
                has_template = False
                
            if not has_template:
                # No template, use standard process
                self._process_standard_payroll(payroll, employee)
            
            # Update payroll totals
            update_payroll_totals(payroll)
            payrolls_created.append(payroll)
            
        return len(payrolls_created)
    
    def _process_standard_payroll(self, payroll, employee):
        """Process payroll using standard method without template"""
        # Add standard earnings based on salary type
        if employee.salary_type == 'monthly':
            PayrollEntry.objects.create(
                payroll=payroll,
                name="Base Salary",
                description=f"Monthly base salary ({employee.salary_currency.code})",
                amount=employee.base_salary,
                is_deduction=False
            )
            taxable_amount = employee.base_salary_egp  # Use EGP amount for tax calculation
        else:  # hourly rate
            # Calculate total hours for the period (assuming standard 8 hours/day, 22 days/month)
            standard_hours = 8 * 22  # 176 hours per month
            total_amount = employee.hourly_rate * standard_hours
            
            PayrollEntry.objects.create(
                payroll=payroll,
                name="Hourly Wages",
                description=f"Standard hours ({standard_hours} hrs) @ {employee.hourly_rate} {employee.salary_currency.code}/hr",
                amount=total_amount,
                is_deduction=False
            )
            taxable_amount = employee.hourly_rate_egp * standard_hours  # Use EGP amount for tax calculation
        
        # Calculate and add income tax (always in EGP)
        tax_amount_egp = calculate_income_tax(taxable_amount)
        if tax_amount_egp > Decimal('0.00'):
            # Convert tax amount back to employee's currency
            tax_amount = tax_amount_egp / employee.salary_currency.exchange_rate_to_egp
            PayrollEntry.objects.create(
                payroll=payroll,
                name="Income Tax",
                description=f"Calculated based on tax brackets (converted from {tax_amount_egp} EGP)",
                amount=tax_amount,
                is_deduction=True
            )
        
        # Add loan repayments
        self._add_loan_repayments(payroll, employee)
    
    def _add_loan_repayments(self, payroll, employee):
        """Add loan repayments to payroll"""
        from lending.models import Loan
        # Get active loans only - don't filter by is_fully_paid since it's a property
        active_loans = Loan.objects.filter(
            employee=employee, 
            status=Loan.ACTIVE
        )
        
        for loan in active_loans:
            # Skip fully paid loans - check the property here
            if loan.is_fully_paid:
                continue
                
            # Get next unpaid payment
            next_payment = loan.get_next_payment()
            if next_payment:
                PayrollEntry.objects.create(
                    payroll=payroll,
                    name=f"Loan Repayment - {loan.loan_type}",
                    description=f"Payment {next_payment.payment_number} of {loan.term_months}",
                    amount=next_payment.amount,
                    is_deduction=True
                )
                
                # Mark payment as paid
                next_payment.is_paid = True
                next_payment.paid_date = timezone.now().date()
                next_payment.payroll = payroll
                next_payment.save()
                
                # Check if all payments are paid, update loan status if needed
                if loan.is_fully_paid:
                    loan.status = Loan.COMPLETED
                    loan.actual_end_date = timezone.now().date()
                    loan.save()

class TaxTierListView(LoginRequiredMixin, ListView):
    model = TaxTier
    template_name = 'payroll/tax_tier_list.html'
    context_object_name = 'tax_tiers'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('min_income')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Tax Tiers'
        return context

class TaxTierCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = TaxTier
    form_class = TaxTierForm
    template_name = 'payroll/tax_tier_form.html'
    success_url = reverse_lazy('tax_tier_list')
    permission_required = 'payroll.add_taxtier'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Tax Tier'
        return context
        
    def form_valid(self, form):
        messages.success(self.request, 'Tax tier created successfully.')
        return super().form_valid(form)

class TaxTierUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = TaxTier
    form_class = TaxTierForm
    template_name = 'payroll/tax_tier_form.html'
    success_url = reverse_lazy('tax_tier_list')
    permission_required = 'payroll.change_taxtier'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Tax Tier'
        return context
        
    def form_valid(self, form):
        messages.success(self.request, 'Tax tier updated successfully.')
        return super().form_valid(form)

class TaxTierDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = TaxTier
    template_name = 'payroll/tax_tier_confirm_delete.html'
    success_url = reverse_lazy('tax_tier_list')
    permission_required = 'payroll.delete_taxtier'
    context_object_name = 'tax_tier'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Tax tier deleted successfully.')
        return super().delete(request, *args, **kwargs)

@login_required
@permission_required('payroll.change_payroll')
def bulk_update_payroll_status(request):
    """Update the status of multiple payrolls at once"""
    if request.method == 'POST':
        selected_payrolls = request.POST.getlist('selected_payrolls')
        new_status = request.POST.get('new_status')
        
        if not selected_payrolls:
            messages.warning(request, "No payrolls were selected.")
            return redirect('payroll_list')
            
        if not new_status:
            messages.warning(request, "No status was selected.")
            return redirect('payroll_list')
        
        # Validate status value
        valid_statuses = [status[0] for status in Payroll.STATUS_CHOICES]
        if new_status not in valid_statuses:
            messages.error(request, "Invalid status selected.")
            return redirect('payroll_list')
        
        try:
            with transaction.atomic():
                # Get the payrolls to update
                payrolls = Payroll.objects.filter(id__in=selected_payrolls)
                count = payrolls.count()
                
                # Check if any completed payrolls are being changed to a different status
                completed_being_changed = payrolls.filter(status=Payroll.COMPLETED).exclude(status=new_status).exists()
                if completed_being_changed:
                    messages.warning(
                        request, 
                        "Warning: You are changing the status of completed payrolls. "
                        "This may affect financial records and reports."
                    )
                
                # Update the status
                payrolls.update(status=new_status)
                
                # If status is completed, set the processed_date
                if new_status == Payroll.COMPLETED:
                    # We need to iterate to set processed_date and call save()
                    for payroll in payrolls:
                        if not payroll.processed_date:
                            payroll.processed_date = timezone.now()
                            payroll.save()
                            
                            # Update employee template if moving to completed
                            template = EmployeePayrollTemplate.get_or_create_for_employee(payroll.employee)
                            template.update_from_payroll(payroll)
                
                messages.success(request, f"Updated status to '{new_status}' for {count} payrolls.")
        except Exception as e:
            messages.error(request, f"Error updating payroll statuses: {str(e)}")
    
    return redirect('payroll_list')
