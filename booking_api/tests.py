import json
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Classes, Booking


class FitnessAPITestCase(APITestCase):
    """Base test case with common setup for fitness app tests"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='adminpass123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='userpass123'
        )
        
        self.regular_user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='userpass123'
        )
        
        # Create test classes
        future_time = timezone.now() + timedelta(days=1)
        past_time = timezone.now() - timedelta(days=1)
        
        self.future_class = Classes.objects.create(
            name='Morning Yoga',
            class_type='YOGA',
            instructor='John Doe',
            duration_minutes=60,
            date_time=future_time,
            total_slots=10
        )
        
        self.past_class = Classes.objects.create(
            name='Evening Zumba',
            class_type='ZUMBA',
            instructor='Jane Smith',
            duration_minutes=45,
            date_time=past_time,
            total_slots=15
        )
        
        self.full_class = Classes.objects.create(
            name='HIIT Training',
            class_type='HIIT',
            instructor='Mike Johnson',
            duration_minutes=30,
            date_time=future_time + timedelta(hours=2),
            total_slots=1,
            available_slots=0
        )
    
    def get_jwt_token(self, user):
        """Get JWT token for user authentication"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def authenticate_user(self, user):
        """Set authentication token for requests"""
        token = self.get_jwt_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    def unauthenticate_user(self):
        """Remove authentication credentials"""
        self.client.credentials()


class AuthenticationTestCase(FitnessAPITestCase):
    """Test authentication endpoints"""

    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'admin',
            'password': 'adminpass123'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'admin',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_refresh(self):
        """Test token refresh functionality"""
        refresh = RefreshToken.for_user(self.admin_user)
        url = reverse('token_refresh')
        data = {'refresh': str(refresh)}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


class ClassesTestCase(FitnessAPITestCase):
    """Test class-related endpoints"""
    
    def test_list_classes_authenticated(self):
        """Test listing classes as authenticated user"""
        self.authenticate_user(self.regular_user)
        url = reverse('class-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only future classes
        
    def test_list_classes_unauthenticated(self):
        """Test listing classes without authentication"""
        url = reverse('class-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_classes_filter_by_type(self):
        """Test filtering classes by type"""
        self.authenticate_user(self.regular_user)
        url = reverse('class-list')
        
        response = self.client.get(url, {'type': 'YOGA'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['class_type'], 'YOGA')
    
    def test_list_classes_filter_by_date(self):
        """Test filtering classes by date"""
        self.authenticate_user(self.regular_user)
        url = reverse('class-list')
        date_str = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        response = self.client.get(url, {'date': date_str})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_create_class_as_admin(self):
        """Test creating class as admin user"""
        self.authenticate_user(self.admin_user)
        url = reverse('class-create')
        future_time = timezone.now() + timedelta(days=2)
        
        data = {
            'name': 'Power Yoga',
            'class_type': 'YOGA',
            'instructor': 'Sarah Wilson',
            'duration_minutes': 75,
            'date_time': future_time.strftime('%d/%m/%Y %H:%M'),
            'total_slots': 12
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Classes.objects.filter(name='Power Yoga').count(), 1)
    
    def test_create_class_as_regular_user(self):
        """Test creating class as regular user (should fail)"""
        self.authenticate_user(self.regular_user)
        url = reverse('class-create')
        future_time = timezone.now() + timedelta(days=2)
        
        data = {
            'name': 'Power Yoga',
            'class_type': 'YOGA',
            'instructor': 'Sarah Wilson',
            'duration_minutes': 75,
            'date_time': future_time.strftime('%d/%m/%Y %H:%M'),
            'total_slots': 12
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_class_past_date(self):
        """Test creating class with past date (should fail)"""
        self.authenticate_user(self.admin_user)
        url = reverse('class-create')
        past_time = timezone.now() - timedelta(hours=1)
        
        data = {
            'name': 'Past Class',
            'class_type': 'YOGA',
            'instructor': 'Test Instructor',
            'duration_minutes': 60,
            'date_time': past_time.strftime('%d/%m/%Y %H:%M'),
            'total_slots': 10
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date_time', response.data)
    
    def test_update_class_as_admin(self):
        """Test updating class as admin"""
        self.authenticate_user(self.admin_user)
        url = reverse('class-detail', kwargs={'pk': self.future_class.pk})
        
        data = {
            'name': 'Updated Morning Yoga',
            'class_type': 'YOGA',
            'instructor': 'Updated Instructor',
            'duration_minutes': 90,
            'date_time': self.future_class.date_time.strftime('%d/%m/%Y %H:%M'),
            'total_slots': 15
        }
        
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.future_class.refresh_from_db()
        self.assertEqual(self.future_class.name, 'Updated Morning Yoga')
    
    def test_delete_class_as_admin(self):
        """Test deleting class as admin"""
        self.authenticate_user(self.admin_user)
        url = reverse('class-detail', kwargs={'pk': self.future_class.pk})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Classes.objects.filter(pk=self.future_class.pk).exists())


class BookingTestCase(FitnessAPITestCase):
    """Test booking-related endpoints"""
    
    def test_create_booking_success(self):
        """Test successful booking creation"""
        self.authenticate_user(self.regular_user)
        url = reverse('booking-create')
        
        data = {'fitness_class_id': self.future_class.id}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Booking.objects.filter(
                user=self.regular_user,
                fitness_class=self.future_class,
                status='CONFIRMED'
            ).exists()
        )
        # Check that available slots decreased
        self.future_class.refresh_from_db()
        self.assertEqual(self.future_class.available_slots, 9)
    
    def test_create_booking_duplicate(self):
        """Test creating duplicate booking (should fail)"""
        # Create initial booking
        Booking.objects.create(
            user=self.regular_user,
            fitness_class=self.future_class,
            status='CONFIRMED'
        )
        
        self.authenticate_user(self.regular_user)
        url = reverse('booking-create')
        
        data = {'fitness_class_id': self.future_class.id}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_booking_full_class(self):
        """Test booking a full class (should fail)"""
        self.authenticate_user(self.regular_user)
        url = reverse('booking-create')
        
        data = {'fitness_class_id': self.full_class.id}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_booking_nonexistent_class(self):
        """Test booking nonexistent class"""
        self.authenticate_user(self.regular_user)
        url = reverse('booking-create')
        
        data = {'fitness_class_id': 99999}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_list_bookings_user(self):
        """Test listing user's own bookings"""
        # Create test bookings
        booking1 = Booking.objects.create(
            user=self.regular_user,
            fitness_class=self.future_class,
            status='CONFIRMED'
        )
        booking2 = Booking.objects.create(
            user=self.regular_user2,
            fitness_class=self.future_class,
            status='CONFIRMED'
        )
        
        self.authenticate_user(self.regular_user)
        url = reverse('booking-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only user's own booking
        self.assertEqual(response.data[0]['id'], booking1.id)
    
    def test_list_bookings_admin_all(self):
        """Test admin listing all bookings"""
        booking1 = Booking.objects.create(
            user=self.regular_user,
            fitness_class=self.future_class,
            status='CONFIRMED'
        )
        booking2 = Booking.objects.create(
            user=self.regular_user2,
            fitness_class=self.future_class,
            status='CONFIRMED'
        )
        
        self.authenticate_user(self.admin_user)
        url = reverse('booking-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Admin sees all bookings
    
    def test_list_bookings_admin_filter_by_email(self):
        """Test admin filtering bookings by email"""
        booking1 = Booking.objects.create(
            user=self.regular_user,
            fitness_class=self.future_class,
            status='CONFIRMED'
        )
        booking2 = Booking.objects.create(
            user=self.regular_user2,
            fitness_class=self.future_class,
            status='CONFIRMED'
        )
        
        self.authenticate_user(self.admin_user)
        url = reverse('booking-list')
        
        response = self.client.get(url, {'email': 'user1@test.com'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user']['email'], 'user1@test.com')
    
    def test_list_bookings_admin_filter_by_status(self):
        """Test admin filtering bookings by status"""
        booking1 = Booking.objects.create(
            user=self.regular_user,
            fitness_class=self.future_class,
            status='CONFIRMED'
        )
        booking2 = Booking.objects.create(
            user=self.regular_user2,
            fitness_class=self.future_class,
            status='CANCELLED'
        )
        
        self.authenticate_user(self.admin_user)
        url = reverse('booking-list')
        
        response = self.client.get(url, {'status': 'CONFIRMED'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'CONFIRMED')
    
    def test_cancel_booking_owner(self):
        """Test user cancelling their own booking"""
        booking = Booking.objects.create(
            user=self.regular_user,
            fitness_class=self.future_class,
            status='CONFIRMED'
        )
        initial_slots = self.future_class.available_slots
        
        self.authenticate_user(self.regular_user)
        url = reverse('booking-cancel', kwargs={'pk': booking.pk})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CANCELLED')
        self.assertIsNotNone(booking.cancelled_at)
        
        # Check available slots increased
        self.future_class.refresh_from_db()
        self.assertEqual(self.future_class.available_slots, initial_slots + 1)
    
    def test_cancel_booking_admin(self):
        """Test admin cancelling any booking"""
        booking = Booking.objects.create(
            user=self.regular_user,
            fitness_class=self.future_class,
            status='CONFIRMED'
        )
        
        self.authenticate_user(self.admin_user)
        url = reverse('booking-cancel', kwargs={'pk': booking.pk})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CANCELLED')
    
    def test_cancel_booking_unauthorized(self):
        """Test user trying to cancel another user's booking"""
        booking = Booking.objects.create(
            user=self.regular_user,
            fitness_class=self.future_class,
            status='CONFIRMED'
        )
        
        self.authenticate_user(self.regular_user2)
        url = reverse('booking-cancel', kwargs={'pk': booking.pk})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_cancel_nonexistent_booking(self):
        """Test cancelling nonexistent booking"""
        self.authenticate_user(self.regular_user)
        url = reverse('booking-cancel', kwargs={'pk': 99999})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class StatisticsTestCase(FitnessAPITestCase):
    """Test statistics endpoints"""
    
    def setUp(self):
        super().setUp()
        
        # Create some test data for statistics
        recent_time = timezone.now() - timedelta(days=15)
        old_time = timezone.now() - timedelta(days=45)
        
        self.recent_class = Classes.objects.create(
            name='Recent Class',
            class_type='YOGA',
            instructor='Test Instructor',
            duration_minutes=60,
            date_time=recent_time,
            total_slots=10
        )
        
        self.old_class = Classes.objects.create(
            name='Old Class',
            class_type='ZUMBA',
            instructor='Test Instructor',
            duration_minutes=45,
            date_time=old_time,
            total_slots=10
        )
        
        # Create bookings
        Booking.objects.create(
            user=self.regular_user,
            fitness_class=self.recent_class,
            status='CONFIRMED'
        )
        Booking.objects.create(
            user=self.regular_user2,
            fitness_class=self.recent_class,
            status='CANCELLED'
        )
        Booking.objects.create(
            user=self.regular_user,
            fitness_class=self.old_class,
            status='CONFIRMED'
        )
    
    def test_admin_statistics(self):
        """Test admin statistics endpoint"""
        self.authenticate_user(self.admin_user)
        url = reverse('statistics')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_keys = [
            'total_classes',
            'total_booking',
            'confirmed_bookings',
            'cancelled_bookings',
            'popular_classes'
        ]
        
        for key in expected_keys:
            self.assertIn(key, response.data)
        
        # Should only include recent data (last 30 days)
        self.assertGreaterEqual(response.data['total_classes'], 1)
        self.assertIsInstance(response.data['popular_classes'], list)
    
    def test_admin_statistics_unauthorized(self):
        """Test admin statistics as regular user"""
        self.authenticate_user(self.regular_user)
        url = reverse('statistics')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_user_statistics(self):
        """Test user statistics endpoint"""
        # Create a future booking for upcoming classes count
        future_booking = Booking.objects.create(
            user=self.regular_user,
            fitness_class=self.future_class,
            status='CONFIRMED'
        )
        
        self.authenticate_user(self.regular_user)
        url = reverse('user-statistics')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_keys = [
            'user',
            'bookings',
            'cancelled_bookings',
            'upcoming_classes',
            'upcoming_classes_details'
        ]
        
        for key in expected_keys:
            self.assertIn(key, response.data)
        
        # Verify user data
        self.assertEqual(response.data['user']['email'], self.regular_user.email)
        self.assertGreaterEqual(response.data['bookings'], 1)
        self.assertGreaterEqual(response.data['upcoming_classes'], 1)
        self.assertIsInstance(response.data['upcoming_classes_details'], list)
    
    def test_user_statistics_unauthenticated(self):
        """Test user statistics without authentication"""
        url = reverse('user-statistics')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EdgeCaseTestCase(FitnessAPITestCase):
    """Test edge cases and error conditions"""
    
    def test_malformed_date_filter(self):
        """Test class list with malformed date filter"""
        self.authenticate_user(self.regular_user)
        url = reverse('class-list')
        
        response = self.client.get(url, {'date': 'invalid-date'})
        
        # Should not crash, just ignore invalid date
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_invalid_class_type_filter(self):
        """Test class list with invalid class type"""
        self.authenticate_user(self.regular_user)
        url = reverse('class-list')
        
        response = self.client.get(url, {'type': 'INVALID_TYPE'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_create_class_with_zero_slots(self):
        """Test creating class with zero total slots"""
        self.authenticate_user(self.admin_user)
        url = reverse('class-create')
        future_time = timezone.now() + timedelta(days=1)
        
        data = {
            'name': 'Zero Slots Class',
            'class_type': 'YOGA',
            'instructor': 'Test Instructor',
            'duration_minutes': 60,
            'date_time': future_time.strftime('%d/%m/%Y %H:%M'),
            'total_slots': 0
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('total_slots', response.data)
    
    def test_cancel_already_cancelled_booking(self):
        """Test cancelling an already cancelled booking"""
        booking = Booking.objects.create(
            user=self.regular_user,
            fitness_class=self.future_class,
            status='CANCELLED',
            cancelled_at=timezone.now()
        )
        
        self.authenticate_user(self.regular_user)
        url = reverse('booking-cancel', kwargs={'pk': booking.pk})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PermissionTestCase(FitnessAPITestCase):
    """Test permission enforcement across all endpoints"""
    
    def test_all_endpoints_require_authentication(self):
        """Test that all endpoints require authentication"""
        endpoints = [
            ('class-list', 'get', {}),
            ('class-create', 'post', {}),
            ('booking-create', 'post', {}),
            ('booking-list', 'get', {}),
            ('statistics', 'get', {}),
            ('user-statistics', 'get', {}),
        ]
        
        for endpoint_name, method, kwargs in endpoints:
            url = reverse(endpoint_name, kwargs=kwargs)
            response = getattr(self.client, method)(url)
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f"Endpoint {endpoint_name} should require authentication"
            )
    
    def test_admin_only_endpoints(self):
        """Test that admin-only endpoints reject regular users"""
        admin_endpoints = [
            ('class-create', 'post', {}),
            ('statistics', 'get', {}),
        ]
        
        self.authenticate_user(self.regular_user)
        
        for endpoint_name, method, kwargs in admin_endpoints:
            url = reverse(endpoint_name, kwargs=kwargs)
            response = getattr(self.client, method)(url, {})
            self.assertEqual(
                response.status_code,
                status.HTTP_403_FORBIDDEN,
                f"Endpoint {endpoint_name} should be admin-only"
            )