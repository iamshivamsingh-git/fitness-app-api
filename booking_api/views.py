from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response

from .models import Classes, Booking
from .serializers import UserSerializer, ClassesSerializer, BookingSerializer
from .permissions import IsAdminOrOwner

from django.db.models import Count, Q 
from datetime import date as date_class

import logging

logger = logging.getLogger('booking_api')

class ClassListView(generics.ListAPIView):
    """ Return list of all the upcoming classes [GET /classes] """
    serializer_class = ClassesSerializer
    permission_classes = [AllowAny]  # Allow any user to view classes

    def get_queryset(self):
        queryset = Classes.objects.filter(date_time__gt=timezone.now())

        # Filtering :  1) Type 2) Date
        class_type = self.request.query_params.get('type')
        if class_type:
            queryset = queryset.filter(class_type=class_type)
        
        date = self.request.query_params.get('date')
        if isinstance(date, date_class):
            try:
                queryset = queryset.filter(date_time__date=date)
            except Exception as e:
                logger.error(f"Error filtering by date: {e}")
                pass
        
        return queryset
    
class ClassCreateView(generics.CreateAPIView):
    """ Create new Class (Admin Only) [POST /admin/classes] """
    queryset = Classes.objects.all()
    serializer_class = ClassesSerializer
    permission_classes = [IsAdminUser]
    
    def perform_create(self, serializer):
        logger.info(f"Admin {self.request.user.username} creating new class: {serializer.validated_data['name']}")
        return super().perform_create(serializer)

class ClassUpdateDeleteView(generics.UpdateAPIView, generics.DestroyAPIView):
    """
    Update Classes (Admin Only) [PUT/PATCH /admin/classes/<id>]
    Delete Classes (Admin Only) [DELETE /admin/classes/<id>s]
    """
    queryset = Classes.objects.all()
    serializer_class = ClassesSerializer
    permission_classes = [IsAdminUser]

    def perform_update(self, serializer):
        logger.info(f"Admin {self.request.user.username} updating class: {serializer.validated_data['name']}")
        return super().perform_update(serializer)

    def perform_destroy(self, instance):
        logger.info(f"Admin {self.request.user.username} deleting class: {instance.name}")
        return super().perform_destroy(instance)
    
class BookingCreateView(generics.CreateAPIView):
    """
    Book a class [POST /book] 
    """
    serializer_class = BookingSerializer
    
    def perform_create(self, serializer):
        user = self.request.user
        logger.info(f"User {user.username} is booking a class.")
        serializer.save(user=user)

class BookingListView(generics.ListAPIView):
    """
    List all bookings of the user [GET /booking | /booking/?email=<email>&status=<status> (Admin Only)] 
    """
    serializer_class = BookingSerializer
    
    def get_queryset(self):
        user = self.request.user
        # Prefetch user for efficiency
        queryset = Booking.objects.select_related('user').all()
        # If user is not admin, filter bookings by user
        if not user.is_staff:
            logger.info(f"User {user.username} is listing their bookings.")
            return queryset.filter(user=user)
        # If user is admin, allow filtering by email
        email = self.request.query_params.get('email')
        if email:
            logger.info(f"Admin {user.username} is listing bookings for user email: {email}")
            queryset = queryset.filter(user__email=email)
        # Allow filtering by status
        status = self.request.query_params.get("status")
        if status:
            logger.info(f"Filtering bookings by status: {status}")
            queryset = queryset.filter(status__iexact=status)
        return queryset
    
class BookingCancelView(APIView):
    """
    Cancel a booking [POST /bookings/<pk>/cancel]
    """
    permission_classes = [IsAdminOrOwner]
    def post(self, request, pk):
        # Get the booking object or return 404
        booking = get_object_or_404(Booking, pk=pk)
        # Check permissions (admin or owner)
        self.check_object_permissions(request, booking)
        # Attempt to cancel the booking
        cancel_status = booking.cancel()
        if not cancel_status:
            logger.warning(f"Booking cancellation failed for booking ID {pk} by user {request.user.username}.")
            return Response({"error": "Booking is already cancelled or not confirmed."}, status=status.HTTP_400_BAD_REQUEST)
        logger.info(f"Booking ID {pk} cancelled successfully by user {request.user.username}.")
        return Response({"message": "Booking cancelled successfully."}, status=status.HTTP_200_OK)
    
class StatisticsView(APIView):
    """
    Get statistics of classes [GET /classes/statistics]
    """
    permission_classes = [IsAdminUser]
    def get(self, request):
        # Statistics for last 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        # Count distinct classes in the last 30 days
        total_classes = Classes.objects.filter(date_time__gte=thirty_days_ago).count()
        # Aggregate count data for bookings in the last 30 days
        booking_counts = Booking.objects.filter(booked_at__gte=thirty_days_ago).aggregate(
            total_booking=Count('id', filter=Q(status__in=['CONFIRMED', 'CANCELLED'])),
            confirmed_bookings=Count('id', filter=Q(status='CONFIRMED')),
            cancelled_bookings=Count('id', filter=Q(status='CANCELLED')),
        )

        # Get the top 5 most popular classes by confirmed bookings
        popular_classes = list(
            Classes.objects.filter(date_time__gte=thirty_days_ago)
            .annotate(booking_count=Count('class_bookings', filter=Q(class_bookings__status='CONFIRMED')))
            .order_by('-booking_count')[:5]
            .values("name", "class_type", "instructor", "booking_count")
        )
        logger.info(f"Statistics requested by admin {request.user.username}")
        data = {
            'total_classes': total_classes,
            **booking_counts,
            'popular_classes': popular_classes,
        }
        return Response(data, status=200)

class UserStatisticsView(APIView):
    """
    Get user profile information [GET /user/profile]
    """
    def get(self, request):
        user = request.user
        # Aggregate booking counts for the user
        counts = Booking.objects.filter(user=user).aggregate(
            bookings=Count('id', filter=Q(status='CONFIRMED')),
            cancelled_bookings=Count('id', filter=Q(status='CANCELLED')),
            upcoming_classes=Count('id', filter=Q(status='CONFIRMED', fitness_class__date_time__gt=timezone.now()))
        )
        # Get details of the next 5 upcoming classes for the user
        upcoming = Booking.objects.filter(
            user=user,
            status='CONFIRMED',
            fitness_class__date_time__gt=timezone.now()
        ).select_related('fitness_class').order_by('fitness_class__date_time')[:5]
        upcoming_classes = [
            {
                'name': b.fitness_class.name,   
                'class_type': b.fitness_class.class_type,
                'duration_minutes': b.fitness_class.duration_minutes,
                'date_time': b.fitness_class.date_time,
                'instructor': b.fitness_class.instructor
            }
            for b in upcoming
        ]
        logger.info(f"User {user.username} requested their profile statistics.")
        data = {
            'user': UserSerializer(user).data,
            **counts,
            'upcoming_classes_details': upcoming_classes
        }
        return Response(data, status=200)


