from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Sum, Q, F, ExpressionWrapper, DecimalField
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from employees.models import Employee
from .models import Loan, LoanPayment, LoanType
from .forms import LoanForm, LoanRepaymentForm, LoanTypeForm, LoanApprovalForm

# Constants
LOAN_REPAYMENT_FORM_TEMPLATE = 'lending/loan_repayment_form.html'
LOAN_LIST_TEMPLATE = 'lending/loan_list.html'
LOAN_DETAIL_TEMPLATE = 'lending/loan_detail.html'
LOAN_FORM_TEMPLATE = 'lending/loan_form.html'
LOAN_CONFIRM_DELETE_TEMPLATE = 'lending/loan_confirm_delete.html'
LOAN_APPROVAL_FORM_TEMPLATE = 'lending/loan_approval_form.html'
LOAN_REJECT_FORM_TEMPLATE = 'lending/loan_reject_form.html'
LOAN_REPAYMENT_CONFIRM_DELETE_TEMPLATE = 'lending/loan_repayment_confirm_delete.html'
LOAN_TYPE_LIST_TEMPLATE = 'lending/loan_type_list.html'
LOAN_TYPE_FORM_TEMPLATE = 'lending/loan_type_form.html'
LOAN_TYPE_CONFIRM_DELETE_TEMPLATE = 'lending/loan_type_confirm_delete.html'

class LoanListView(LoginRequiredMixin, ListView):
    model = Loan
    template_name = LOAN_LIST_TEMPLATE
    context_object_name = 'loans'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Regular employees can only see their own loans
        if not self.request.user.is_superuser:
            try:
                employee = Employee.objects.get(user=self.request.user)
                queryset = queryset.filter(employee=employee)
            except Employee.DoesNotExist:
                return Loan.objects.none()
                
        search_query = self.request.GET.get('search', '')
        status = self.request.GET.get('status', '')
        
        if search_query:
            queryset = queryset.filter(
                Q(employee__first_name__icontains=search_query) | 
                Q(employee__last_name__icontains=search_query) |
                Q(employee__employee_id__icontains=search_query) |
                Q(loan_id__icontains=search_query) |
                Q(loan_type__name__icontains=search_query)
            )
            
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.select_related('employee', 'loan_type')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Loan.STATUS_CHOICES
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        
        # Summary statistics
        loans = self.get_queryset()
        context['total_loans'] = loans.count()
        context['total_amount'] = loans.aggregate(total=Sum('amount'))['total'] or 0
        context['total_pending'] = loans.filter(status='pending').count()
        context['total_active'] = loans.filter(status='active').count()
        
        # Calculate remaining balance for active loans
        active_loans = loans.filter(status='active')
        total_remaining = Decimal('0.00')
        
        for loan in active_loans:
            total_remaining += loan.remaining_balance
            
        context['total_remaining'] = total_remaining
        
        return context

class LoanDetailView(LoginRequiredMixin, DetailView):
    model = Loan
    template_name = LOAN_DETAIL_TEMPLATE
    context_object_name = 'loan'
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Regular employees can only view their own loans
        if not self.request.user.is_superuser:
            try:
                employee = Employee.objects.get(user=self.request.user)
                if obj.employee != employee:
                    raise Http404("You don't have permission to view this loan.")
            except Employee.DoesNotExist:
                raise Http404("Employee profile not found.")
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        loan = self.get_object()
        
        # Get repayments
        context['repayments'] = loan.repayments.all().order_by('-payment_date')
        
        # Calculate remaining balance 
        context['remaining_balance'] = loan.remaining_balance
        
        # Calculate progress percentage
        if loan.amount > 0:
            context['repayment_progress'] = ((loan.amount - loan.remaining_balance) / loan.amount) * 100
        else:
            context['repayment_progress'] = 0
            
        # Add approval form for pending loans
        if loan.status == 'pending':
            context['approval_form'] = LoanApprovalForm(instance=loan)
            
        return context

class LoanCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Loan
    form_class = LoanForm
    template_name = LOAN_FORM_TEMPLATE
    success_url = reverse_lazy('loan_list')
    permission_required = 'lending.add_loan'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Apply for Loan'
        context['button_label'] = 'Submit Loan Application'
        return context
    
    def form_valid(self, form):
        with transaction.atomic():
            loan = form.save(commit=False)
            
            # Set default values for new loans
            loan.status = 'pending'
            loan.start_date = None  # Will be set upon approval
            
            # Generate a unique loan ID
            loan.loan_id = f"LOAN-{timezone.now().strftime('%Y%m%d')}-{loan.employee.employee_id}"
            
            loan.save()
            
            messages.success(self.request, "Loan application submitted successfully. Awaiting approval.")
            return super().form_valid(form)

class LoanUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Loan
    form_class = LoanForm
    template_name = LOAN_FORM_TEMPLATE
    permission_required = 'lending.change_loan'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Loan'
        context['button_label'] = 'Update Loan Details'
        
        # Don't allow editing status through the form
        if 'status' in context['form'].fields:
            context['form'].fields['status'].disabled = True
            
        return context
    
    def get_success_url(self):
        return reverse('loan_detail', args=[self.object.pk])
    
    def form_valid(self, form):
        with transaction.atomic():
            loan = form.save(commit=False)
            
            # Ensure status doesn't change through the form
            original_loan = Loan.objects.get(pk=loan.pk)
            loan.status = original_loan.status
            
            loan.save()
            
            messages.success(self.request, "Loan updated successfully.")
            return super().form_valid(form)

class LoanDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Loan
    template_name = LOAN_CONFIRM_DELETE_TEMPLATE
    success_url = reverse_lazy('loan_list')
    permission_required = 'lending.delete_loan'
    context_object_name = 'loan'
    
    def delete(self, request, *args, **kwargs):
        loan = self.get_object()
        
        # Don't allow deleting active or completed loans
        if loan.status in ['active', 'completed']:
            messages.error(request, "Cannot delete an active or completed loan.")
            return redirect('loan_detail', pk=loan.pk)
            
        # Delete associated repayments
        LoanPayment.objects.filter(loan=loan).delete()
        
        messages.success(request, "Loan deleted successfully.")
        return super().delete(request, *args, **kwargs)

@login_required
@permission_required('lending.change_loan')
def approve_loan(request, pk):
    loan = get_object_or_404(Loan, pk=pk)
    
    if loan.status != 'pending':
        messages.error(request, "This loan is not pending approval.")
        return redirect('loan_detail', pk=loan.pk)
    
    if request.method == 'POST':
        form = LoanApprovalForm(request.POST, instance=loan)
        if form.is_valid():
            with transaction.atomic():
                # Set loan details
                loan = form.save(commit=False)
                loan.status = 'active'
                loan.start_date = timezone.now().date()
                
                # If not specified, set end date based on term length
                if not loan.end_date and loan.term_months:
                    loan.end_date = loan.start_date.replace(
                        month=((loan.start_date.month + loan.term_months - 1) % 12) + 1,
                        year=loan.start_date.year + ((loan.start_date.month + loan.term_months - 1) // 12)
                    )
                
                loan.approved_by = request.user
                loan.approval_date = timezone.now()
                loan.save()
                
                messages.success(request, "Loan approved successfully.")
                return redirect('loan_detail', pk=loan.pk)
    else:
        form = LoanApprovalForm(instance=loan)
    
    return render(request, LOAN_APPROVAL_FORM_TEMPLATE, {
        'form': form,
        'loan': loan
    })

@login_required
@permission_required('lending.change_loan')
def reject_loan(request, pk):
    loan = get_object_or_404(Loan, pk=pk)
    
    if loan.status != 'pending':
        messages.error(request, "This loan is not pending approval.")
        return redirect('loan_detail', pk=loan.pk)
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '')
        
        with transaction.atomic():
            loan.status = 'rejected'
            loan.rejection_reason = rejection_reason
            loan.approved_by = request.user
            loan.approval_date = timezone.now()
            loan.save()
            
            messages.success(request, "Loan rejected successfully.")
            return redirect('loan_detail', pk=loan.pk)
    
    return render(request, LOAN_REJECT_FORM_TEMPLATE, {'loan': loan})

@login_required
@permission_required('lending.add_loanrepayment')
def add_loan_repayment(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    
    if loan.status != 'active':
        messages.error(request, "Cannot add repayment to a loan that is not active.")
        return redirect('loan_detail', pk=loan.id)
    
    if request.method == 'POST':
        form = LoanRepaymentForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                repayment = form.save(commit=False)
                repayment.loan = loan
                
                # Check if amount is valid (not greater than remaining balance)
                if repayment.amount > loan.remaining_balance:
                    form.add_error('amount', f"Amount exceeds remaining balance (${loan.remaining_balance}).")
                    return render(request, LOAN_REPAYMENT_FORM_TEMPLATE, {
                        'form': form,
                        'loan': loan,
                        'title': 'Add Loan Repayment'
                    })
                
                repayment.save()
                
                # Check if loan is fully repaid
                if loan.remaining_balance <= Decimal('0.01'):  # Using small epsilon for floating point
                    loan.status = 'completed'
                    loan.completion_date = timezone.now().date()
                    loan.save()
                    messages.success(request, "Loan has been fully repaid and marked as completed.")
                
                messages.success(request, "Repayment added successfully.")
                return redirect('loan_detail', pk=loan.id)
    else:
        # Pre-fill with remaining balance as default amount
        initial_data = {
            'payment_date': timezone.now().date(),
            'amount': loan.remaining_balance
        }
        form = LoanRepaymentForm(initial=initial_data)
    
    return render(request, LOAN_REPAYMENT_FORM_TEMPLATE, {
        'form': form,
        'loan': loan,
        'title': 'Add Loan Repayment'
    })

@login_required
@permission_required('lending.change_loanrepayment')
def edit_loan_repayment(request, repayment_id):
    repayment = get_object_or_404(LoanPayment, id=repayment_id)
    loan = repayment.loan
    
    if loan.status == 'completed' and repayment.payment_date < loan.completion_date:
        messages.error(request, "Cannot edit repayments for completed loans.")
        return redirect('loan_detail', pk=loan.id)
    
    original_amount = repayment.amount
    
    if request.method == 'POST':
        form = LoanRepaymentForm(request.POST, instance=repayment)
        if form.is_valid():
            with transaction.atomic():
                # Calculate what the remaining balance would be with the new amount
                new_amount = form.cleaned_data['amount']
                amount_difference = new_amount - original_amount
                
                # If amount decreased, check that loan isn't already fully repaid
                # If amount increased, check that it doesn't exceed the original loan amount
                if amount_difference > 0 and (loan.remaining_balance - amount_difference) < 0:
                    form.add_error('amount', "This amount would exceed the total loan amount.")
                    return render(request, LOAN_REPAYMENT_FORM_TEMPLATE, {
                        'form': form,
                        'loan': loan,
                        'repayment': repayment,
                        'title': 'Edit Loan Repayment'
                    })
                
                repayment = form.save()
                
                # Update loan status based on remaining balance
                if loan.remaining_balance <= Decimal('0.01'):
                    if loan.status != 'completed':
                        loan.status = 'completed'
                        loan.completion_date = timezone.now().date()
                        loan.save()
                elif loan.status == 'completed':
                    # If no longer fully repaid, reactivate
                    loan.status = 'active'
                    loan.completion_date = None
                    loan.save()
                
                messages.success(request, "Repayment updated successfully.")
                return redirect('loan_detail', pk=loan.id)
    else:
        form = LoanRepaymentForm(instance=repayment)
    
    return render(request, LOAN_REPAYMENT_FORM_TEMPLATE, {
        'form': form,
        'loan': loan,
        'repayment': repayment,
        'title': 'Edit Loan Repayment'
    })

@login_required
@permission_required('lending.delete_loanrepayment')
def delete_loan_repayment(request, repayment_id):
    repayment = get_object_or_404(LoanPayment, id=repayment_id)
    loan = repayment.loan
    
    if loan.status == 'completed' and repayment.payment_date < loan.completion_date:
        messages.error(request, "Cannot delete repayments for completed loans.")
        return redirect('loan_detail', pk=loan.id)
    
    if request.method == 'POST':
        with transaction.atomic():
            repayment.delete()
            
            # Update loan status if needed
            if loan.status == 'completed' and loan.remaining_balance > Decimal('0.01'):
                loan.status = 'active'
                loan.completion_date = None
                loan.save()
            
            messages.success(request, "Repayment deleted successfully.")
            return redirect('loan_detail', pk=loan.id)
    
    return render(request, LOAN_REPAYMENT_CONFIRM_DELETE_TEMPLATE, {
        'repayment': repayment,
        'loan': loan
    })

# Loan Type Views
class LoanTypeListView(LoginRequiredMixin, ListView):
    model = LoanType
    template_name = LOAN_TYPE_LIST_TEMPLATE
    context_object_name = 'loan_types'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        show_inactive = self.request.GET.get('show_inactive', False)
        
        if not show_inactive:
            queryset = queryset.filter(is_active=True)
            
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_inactive'] = self.request.GET.get('show_inactive', False)
        return context

class LoanTypeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = LoanType
    form_class = LoanTypeForm
    template_name = LOAN_TYPE_FORM_TEMPLATE
    success_url = reverse_lazy('loan_type_list')
    permission_required = 'lending.add_loantype'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Loan Type'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Loan type created successfully.")
        return super().form_valid(form)

class LoanTypeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = LoanType
    form_class = LoanTypeForm
    template_name = LOAN_TYPE_FORM_TEMPLATE
    success_url = reverse_lazy('loan_type_list')
    permission_required = 'lending.change_loantype'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Loan Type'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Loan type updated successfully.")
        return super().form_valid(form)

class LoanTypeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = LoanType
    template_name = LOAN_TYPE_CONFIRM_DELETE_TEMPLATE
    success_url = reverse_lazy('loan_type_list')
    permission_required = 'lending.delete_loantype'
    
    def delete(self, request, *args, **kwargs):
        loan_type = self.get_object()
        
        # Check if there are any loans using this type
        if Loan.objects.filter(loan_type=loan_type).exists():
            messages.error(request, "Cannot delete loan type that is associated with loans.")
            return redirect('loan_type_list')
            
        messages.success(request, "Loan type deleted successfully.")
        return super().delete(request, *args, **kwargs)
