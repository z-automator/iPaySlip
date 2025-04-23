from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import date, timedelta
from .models import Leave


class LeaveModelTests(TestCase):
    """Tests for the Leave model"""
    
    def setUp(self):
        # Create test users
        self.regular_user = User.objects.create_user(
            username='employee1',
            email='employee1@example.com',
            password='password123',
            first_name='John',
            last_name='Doe'
        )
        
        self.staff_user = User.objects.create_user(
            username='manager1',
            email='manager1@example.com',
            password='password123',
            first_name='Jane',
            last_name='Smith',
            is_staff=True
        )
        
        # Create test leave
        self.leave = Leave.objects.create(
            employee=self.regular_user,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            leave_type='vacation',
            reason='Family trip'
        )
    
    def test_leave_creation(self):
        """Test that a leave can be created with valid data"""
        self.assertEqual(self.leave.status, 'pending')
        self.assertEqual(self.leave.leave_type, 'vacation')
        self.assertEqual(self.leave.employee, self.regular_user)
    
    def test_leave_string_representation(self):
        """Test the string representation of a leave"""
        expected_string = f"{self.regular_user.get_full_name()} - Vacation ({self.leave.start_date} to {self.leave.end_date})"
        self.assertEqual(str(self.leave), expected_string)
    
    def test_end_date_validation(self):
        """Test that end_date must be after start_date"""
        invalid_leave = Leave(
            employee=self.regular_user,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=5),  # End date before start date
            leave_type='sick'
        )
        
        # Should raise ValidationError
        with self.assertRaises(Exception):
            invalid_leave.full_clean()
    
    def test_overlapping_dates_validation(self):
        """Test that overlapping leave dates are not allowed"""
        # Create a leave with overlapping dates
        overlapping_leave = Leave(
            employee=self.regular_user,
            start_date=date.today() + timedelta(days=12),  # Overlaps with existing leave
            end_date=date.today() + timedelta(days=17),
            leave_type='sick'
        )
        
        # Should raise ValidationError
        with self.assertRaises(Exception):
            overlapping_leave.full_clean()


class LeaveAPITests(APITestCase):
    """Tests for the Leave API endpoints"""
    
    def setUp(self):
        # Create test users
        self.regular_user = User.objects.create_user(
            username='employee1',
            email='employee1@example.com',
            password='password123',
            first_name='John',
            last_name='Doe'
        )
        
        self.another_user = User.objects.create_user(
            username='employee2',
            email='employee2@example.com',
            password='password123',
            first_name='Bob',
            last_name='Johnson'
        )
        
        self.staff_user = User.objects.create_user(
            username='manager1',
            email='manager1@example.com',
            password='password123',
            first_name='Jane',
            last_name='Smith',
            is_staff=True
        )
        
        # Create test leaves
        self.leave1 = Leave.objects.create(
            employee=self.regular_user,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            leave_type='vacation',
            reason='Family trip'
        )
        
        self.leave2 = Leave.objects.create(
            employee=self.another_user,
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=25),
            leave_type='sick',
            reason='Medical appointment'
        )
        
        # Set up API client
        self.client = APIClient()
        self.list_url = reverse('leave-list')
        self.detail_url = reverse('leave-detail', kwargs={'pk': self.leave1.pk})
    
    def test_list_leaves_as_regular_user(self):
        """Test that regular users can only see their own leaves"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should only see their own leave
        self.assertEqual(response.data[0]['id'], self.leave1.id)
    
    def test_list_leaves_as_staff(self):
        """Test that staff users can see all leaves"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Should see all leaves
    
    def test_create_leave_as_regular_user(self):
        """Test that regular users can create leaves for themselves"""
        self.client.force_authenticate(user=self.regular_user)
        
        data = {
            'start_date': str(date.today() + timedelta(days=30)),
            'end_date': str(date.today() + timedelta(days=35)),
            'leave_type': 'vacation',
            'reason': 'Vacation trip'
        }
        
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['employee']['id'], self.regular_user.id)
        self.assertEqual(response.data['status'], 'pending')
    
    def test_regular_user_cannot_modify_another_users_leave(self):
        """Test that regular users cannot modify another user's leave"""
        self.client.force_authenticate(user=self.regular_user)
        
        other_leave_url = reverse('leave-detail', kwargs={'pk': self.leave2.pk})
        response = self.client.get(other_leave_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # Should not be able to see it
    
    def test_staff_can_change_status(self):
        """Test that staff users can change the status of a leave"""
        self.client.force_authenticate(user=self.staff_user)
        
        data = {'status': 'approved'}
        response = self.client.patch(self.detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'approved')
    
    def test_regular_user_cannot_change_status(self):
        """Test that regular users cannot change the status of their own leave"""
        self.client.force_authenticate(user=self.regular_user)
        
        data = {'status': 'approved'}
        response = self.client.patch(self.detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify status hasn't changed
        updated_leave = Leave.objects.get(pk=self.leave1.pk)
        self.assertEqual(updated_leave.status, 'pending')
