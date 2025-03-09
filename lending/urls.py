from django.urls import path
from .views import (
    LoanListView,
    LoanDetailView,
    LoanCreateView,
    LoanUpdateView,
    LoanDeleteView,
    approve_loan,
    reject_loan,
    LoanTypeListView,
    LoanTypeCreateView,
    LoanTypeUpdateView,
    LoanTypeDeleteView,
)

urlpatterns = [
    path('', LoanListView.as_view(), name='loan_list'),
    path('<int:pk>/', LoanDetailView.as_view(), name='loan_detail'),
    path('create/', LoanCreateView.as_view(), name='loan_create'),
    path('<int:pk>/edit/', LoanUpdateView.as_view(), name='loan_update'),
    path('<int:pk>/delete/', LoanDeleteView.as_view(), name='loan_delete'),
    path('<int:pk>/approve/', approve_loan, name='approve_loan'),
    path('<int:pk>/reject/', reject_loan, name='reject_loan'),
    
    # Loan Type URLs
    path('types/', LoanTypeListView.as_view(), name='loan_type_list'),
    path('types/create/', LoanTypeCreateView.as_view(), name='loan_type_create'),
    path('types/<int:pk>/edit/', LoanTypeUpdateView.as_view(), name='loan_type_update'),
    path('types/<int:pk>/delete/', LoanTypeDeleteView.as_view(), name='loan_type_delete'),
] 