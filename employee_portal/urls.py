from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.employee_dashboard, name='employee_dashboard'),
    
    # Payroll URLs
    path('payrolls/', views.PayrollListView.as_view(), name='employee_payroll_list'),
    path('payrolls/<int:pk>/', views.PayrollDetailView.as_view(), name='employee_payroll_detail'),
    
    # Loan URLs
    path('loans/', views.LoanListView.as_view(), name='employee_loan_list'),
    path('loans/<int:pk>/', views.LoanDetailView.as_view(), name='employee_loan_detail'),
    path('loans/request/', views.LoanRequestView.as_view(), name='employee_loan_request'),
    
    # Leave Request URLs
    path('leaves/', views.LeaveRequestListView.as_view(), name='employee_leave_request_list'),
    path('leaves/<int:pk>/', views.LeaveRequestDetailView.as_view(), name='employee_leave_request_detail'),
    path('leaves/request/', views.LeaveRequestCreateView.as_view(), name='employee_leave_request_create'),
]
