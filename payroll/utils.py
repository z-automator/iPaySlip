from django.template.loader import render_to_string
from django.http import HttpResponse
from django.conf import settings
import os
import io
from xhtml2pdf import pisa
from decimal import Decimal
from .models import TaxTier

def generate_payslip_pdf(payroll, template_name='payroll/pdf/payslip.html'):
    """
    Generate PDF payslip from payroll object using xhtml2pdf
    
    Args:
        payroll: Payroll model instance
        template_name: template to use for PDF generation
        
    Returns:
        HttpResponse with PDF content
    """
    # Get company info from settings
    company_info = {
        'name': settings.COMPANY_NAME,
        'address': settings.COMPANY_ADDRESS,
        'phone': settings.COMPANY_PHONE,
        'email': settings.COMPANY_EMAIL,
        'website': settings.COMPANY_WEBSITE,
        'logo_path': os.path.join(settings.STATIC_ROOT, settings.COMPANY_LOGO)
    }
    
    # Prepare context for template
    context = {
        'payroll': payroll,
        'entries': payroll.entries.all(),
        'earnings': payroll.entries.filter(is_deduction=False),
        'deductions': payroll.entries.filter(is_deduction=True),
        'company': company_info,
    }
    
    # Render HTML content
    html_string = render_to_string(template_name, context)
    
    # Create a file-like buffer to receive PDF data
    buffer = io.BytesIO()
    
    # Generate PDF from HTML content with xhtml2pdf
    pisa_status = pisa.CreatePDF(
        html_string,
        dest=buffer,
        # You can add custom CSS here
        link_callback=link_callback
    )
    
    # Handle errors
    if pisa_status.err:
        return HttpResponse('PDF generation error: %s' % pisa_status.err, content_type='text/plain')
    
    # FileResponse sets the Content-Disposition header
    buffer.seek(0)
    
    # Create HTTP response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"payslip_{payroll.employee.employee_id}_{payroll.period.name}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response

def generate_payroll_report(payrolls, template_name='payroll/pdf/payroll_report.html'):
    """
    Generate PDF report for multiple payrolls using xhtml2pdf
    
    Args:
        payrolls: QuerySet of Payroll objects
        template_name: template to use for PDF generation
        
    Returns:
        HttpResponse with PDF content
    """
    # Get company info from settings
    company_info = {
        'name': settings.COMPANY_NAME,
        'address': settings.COMPANY_ADDRESS,
        'phone': settings.COMPANY_PHONE,
        'email': settings.COMPANY_EMAIL,
        'website': settings.COMPANY_WEBSITE,
        'logo_path': os.path.join(settings.STATIC_ROOT, settings.COMPANY_LOGO)
    }
    
    # Prepare context for template
    context = {
        'payrolls': payrolls,
        'company': company_info,
        'total_gross': sum(p.gross_salary for p in payrolls),
        'total_deductions': sum(p.total_deductions for p in payrolls),
        'total_net': sum(p.net_salary for p in payrolls),
    }
    
    # Get period info from the first payroll (assuming all are from same period)
    if payrolls.exists():
        context['period'] = payrolls.first().period
    
    # Render HTML content
    html_string = render_to_string(template_name, context)
    
    # Create a file-like buffer to receive PDF data
    buffer = io.BytesIO()
    
    # Generate PDF from HTML content with xhtml2pdf
    pisa_status = pisa.CreatePDF(
        html_string,
        dest=buffer,
        # You can add custom CSS here
        link_callback=link_callback
    )
    
    # Handle errors
    if pisa_status.err:
        return HttpResponse('PDF generation error: %s' % pisa_status.err, content_type='text/plain')
    
    # FileResponse sets the Content-Disposition header
    buffer.seek(0)
    
    # Create HTTP response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = "payroll_report.pdf"
    if 'period' in context:
        filename = f"payroll_report_{context['period'].name}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response

def generate_loan_statement(loan, payments=None, template_name='lending/pdf/loan_statement.html'):
    """
    Generate PDF loan statement using xhtml2pdf
    
    Args:
        loan: Loan model instance
        payments: Optional QuerySet of LoanPayment objects
        template_name: template to use for PDF generation
        
    Returns:
        HttpResponse with PDF content
    """
    # Get company info from settings
    company_info = {
        'name': settings.COMPANY_NAME,
        'address': settings.COMPANY_ADDRESS,
        'phone': settings.COMPANY_PHONE,
        'email': settings.COMPANY_EMAIL,
        'website': settings.COMPANY_WEBSITE,
        'logo_path': os.path.join(settings.STATIC_ROOT, settings.COMPANY_LOGO)
    }
    
    # Get payments if not provided
    if payments is None:
        payments = loan.payments.all().order_by('payment_date')
    
    # Calculate summary statistics
    total_paid = sum(payment.amount for payment in payments if payment.is_paid)
    remaining_balance = loan.total_payable - total_paid
    payment_progress = (total_paid / loan.total_payable) * 100 if loan.total_payable else 0
    
    # Prepare context for template
    context = {
        'loan': loan,
        'company': company_info,
        'payments': payments,
        'total_paid': total_paid,
        'remaining_balance': remaining_balance,
        'payment_progress': payment_progress,
        'completed_payments': payments.filter(is_paid=True).count(),
        'pending_payments': payments.filter(is_paid=False).count(),
    }
    
    # Render HTML content
    html_string = render_to_string(template_name, context)
    
    # Create a file-like buffer to receive PDF data
    buffer = io.BytesIO()
    
    # Generate PDF from HTML content with xhtml2pdf
    pisa_status = pisa.CreatePDF(
        html_string,
        dest=buffer,
        # You can add custom CSS here
        link_callback=link_callback
    )
    
    # Handle errors
    if pisa_status.err:
        return HttpResponse('PDF generation error: %s' % pisa_status.err, content_type='text/plain')
    
    # FileResponse sets the Content-Disposition header
    buffer.seek(0)
    
    # Create HTTP response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"loan_statement_{loan.employee.employee_id}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response

def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those resources
    
    Args:
        uri: URI to convert
        rel: path to document being converted
        
    Returns:
        Path to file
    """
    # Use settings.STATIC_ROOT and settings.MEDIA_ROOT to resolve paths
    if uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
    elif uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    else:
        return uri  # Handle other types of URIs
    
    # Make sure the path exists
    if not os.path.isfile(path):
        # Instead of raising an exception, return the URI as is
        # This allows the PDF generation to continue even if some resources are missing
        print(f"Warning: File not found: {path}")
        return uri
    
    return path

def calculate_income_tax(gross_income):
    """
    Calculate income tax based on tax tiers using a progressive tax model
    
    Args:
        gross_income: Decimal or float representing the gross income
        
    Returns:
        Decimal: The calculated tax amount
    """
    # Convert to Decimal if not already
    if not isinstance(gross_income, Decimal):
        gross_income = Decimal(str(gross_income))
    
    # Get all active tax tiers ordered by min_income
    tax_tiers = TaxTier.objects.filter(is_active=True).order_by('min_income')
    
    # If no tax tiers defined, return 0
    if not tax_tiers.exists():
        return Decimal('0.00')
    
    total_tax = Decimal('0.00')
    remaining_income = gross_income
    
    # Process each tier
    for i, tier in enumerate(tax_tiers):
        # If we've used up all income, break
        if remaining_income <= 0:
            break
            
        # Calculate the upper bound for this tier
        if tier.max_income > 0:
            upper_bound = tier.max_income
        else:
            # If this is the highest tier (no upper bound)
            upper_bound = remaining_income + tier.min_income
        
        # Calculate taxable amount in this tier
        if i == 0:
            # First tier
            if gross_income <= upper_bound:
                taxable_in_tier = gross_income - tier.min_income
            else:
                taxable_in_tier = upper_bound - tier.min_income
        else:
            # Subsequent tiers
            if gross_income <= upper_bound:
                taxable_in_tier = gross_income - tier.min_income
            else:
                taxable_in_tier = upper_bound - tier.min_income
                
        # Ensure taxable amount is not negative
        taxable_in_tier = max(Decimal('0.00'), taxable_in_tier)
        
        # Calculate tax for this tier
        tax_rate = tier.rate / Decimal('100.00')
        tax_for_tier = taxable_in_tier * tax_rate
        
        # Add to total tax
        total_tax += tax_for_tier
        
        # Reduce remaining income
        remaining_income -= taxable_in_tier
    
    # Round to 2 decimal places
    return total_tax.quantize(Decimal('0.01')) 