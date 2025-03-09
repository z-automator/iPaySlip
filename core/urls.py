from django.urls import path
from . import views

# Remove the app_name to make the URL pattern available without a namespace
# app_name = 'core'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
] 