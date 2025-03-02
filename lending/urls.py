from django.urls import path
from .views import (
    LoanListView,
    LoanDetailView,
    LoanCreateView,
    LoanUpdateView,
    LoanDeleteView,
    approve_loan,
    reject_loan,
)

urlpatterns = [
    path('', LoanListView.as_view(), name='loan_list'),
    path('<int:pk>/', LoanDetailView.as_view(), name='loan_detail'),
    path('create/', LoanCreateView.as_view(), name='loan_create'),
    path('<int:pk>/edit/', LoanUpdateView.as_view(), name='loan_update'),
    path('<int:pk>/delete/', LoanDeleteView.as_view(), name='loan_delete'),
    path('<int:pk>/approve/', approve_loan, name='approve_loan'),
    path('<int:pk>/reject/', reject_loan, name='reject_loan'),
] 