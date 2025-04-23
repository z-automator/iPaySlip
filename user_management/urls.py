from django.urls import path
from . import views

urlpatterns = [
    # User Role URLs
    path('roles/', views.UserRoleListView.as_view(), name='role_list'),
    path('roles/<int:pk>/', views.UserRoleDetailView.as_view(), name='role_detail'),
    path('roles/create/', views.UserRoleCreateView.as_view(), name='role_create'),
    path('roles/<int:pk>/edit/', views.UserRoleUpdateView.as_view(), name='role_update'),
    path('roles/<int:pk>/delete/', views.UserRoleDeleteView.as_view(), name='role_delete'),
    
    # User Management URLs
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
]
