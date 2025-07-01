from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from booking_api.models import Classes, Booking 

class Command(BaseCommand):
    help = "Seed the database with demo fitness classes, users, and bookings."

    def handle(self, *args, **kwargs):
        # Clear existing (non-superuser) users and classes/bookings
        User.objects.all().delete()
        Classes.objects.all().delete()
        Booking.objects.all().delete()

        now = timezone.now()

        # Create users
        superuser = User.objects.create_superuser(username='admin',email='superadmin@test.com',password='admin')
        admin = User.objects.create_user(username='admin123', email='admin@test.com', password='admin123', is_staff=True)
        user1 = User.objects.create_user(username='user1', email='user1@test.com', password='user123')
        user2 = User.objects.create_user(username='user2', email='user2@test.com', password='user123')

        # Create classes
        yoga_class = Classes.objects.create(
            name='Sunrise Yoga',
            class_type='YOGA',
            instructor='Alice',
            duration_minutes=60,
            date_time=now + timedelta(days=2),
            total_slots=10,
            available_slots=10
        )

        zumba_class = Classes.objects.create(
            name='Evening Zumba',
            class_type='ZUMBA',
            instructor='Bob',
            duration_minutes=45,
            date_time=now + timedelta(days=1),
            total_slots=15,
            available_slots=15
        )

        hiit_class = Classes.objects.create(
            name='HIIT Blast',
            class_type='HIIT',
            instructor='Charlie',
            duration_minutes=30,
            date_time=now - timedelta(days=10),
            total_slots=20,
            available_slots=20
        )

        recent_class = Classes.objects.create(
            name='Recent Stretch',
            class_type='YOGA',
            instructor='Dana',
            duration_minutes=50,
            date_time=now - timedelta(days=5),
            total_slots=10,
            available_slots=10
        )

        # Bookings
        Booking.objects.create(user=user1, fitness_class=yoga_class, status='CONFIRMED')
        yoga_class.available_slots -= 1
        yoga_class.save()

        Booking.objects.create(user=user2, fitness_class=yoga_class, status='CANCELLED')

        Booking.objects.create(user=user1, fitness_class=zumba_class, status='CONFIRMED')
        zumba_class.available_slots -= 1
        zumba_class.save()

        Booking.objects.create(user=user2, fitness_class=zumba_class, status='CONFIRMED')
        zumba_class.available_slots -= 1
        zumba_class.save()

        Booking.objects.create(user=user1, fitness_class=hiit_class, status='CANCELLED')

        Booking.objects.create(user=user2, fitness_class=recent_class, status='CONFIRMED')
        recent_class.available_slots -= 1
        recent_class.save()

        self.stdout.write(self.style.SUCCESS("✅ Seed data created successfully."))
