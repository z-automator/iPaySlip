from django.shortcuts import render

# Create your views here.

def home_view(request):
    """Home page view"""
    return render(request, 'core/home.html', {
        'title': 'Payslip System'
    })
