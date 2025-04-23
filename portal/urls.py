from django.urls import path
from . import views

urlpatterns = [
    path('', views.portal_dashboard, name='portal_dashboard'),
    # Add more portal URLs here as needed
]
