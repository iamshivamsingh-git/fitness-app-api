from .models import Classes, User, Booking
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "password"]
        read_only_fields = [
            "id"
        ]
    def create(self, validated_data):
        # Create a new user with hashed password
        user = User(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class ClassesSerializer(serializers.ModelSerializer):
    # Custom date_time field formatting and parsing
    date_time = serializers.DateTimeField(
        input_formats=['%d/%m/%Y %H:%M'],
        format='%d/%m/%Y %H:%M'
    )
    class Meta:
        model = Classes
        fields = [
            "id", "name", "class_type", "date_time", "instructor",
            "total_slots", 'duration_minutes', "available_slots", 
            'is_available', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            "id", "available_slots", "created_at", "modified_at", "is_available"
        ]

    def validate_date_time(self, value):
        # Ensure the class is scheduled for a future time
        if value <= timezone.now():
            raise serializers.ValidationError("The class must be scheduled for a future time.")
        return value
    
    def validate_total_slots(self, value):
        # Ensure total slots is a positive integer
        if value <= 0:
            raise serializers.ValidationError("Total slots must be a positive integer.")
        return value
    
    def validate(self, attrs):
        # Check for any extra fields not allowed in the serializer
        atts = super().validate(attrs)
        errors = {}
        extra_fields = set(self.initial_data.keys()) - set(self.fields.keys())
        
        for field in extra_fields:
            errors[field] = f"Field '{field}' is not allowed."
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return attrs
    
class BookingSerializer(serializers.ModelSerializer):
    # Nested user and class serializers for read-only representation
    user = UserSerializer(read_only=True)
    fitness_class = ClassesSerializer(read_only=True)
    fitness_class_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'fitness_class', 'fitness_class_id',
            'status', 'booked_at', 'cancelled_at'
        ]
        read_only_fields = ['id', 'user', 'booked_at', 'cancelled_at', 'status', 'fitness_class']

    def validate(self, attrs):
        # Check for any extra fields not allowed in the serializer
        atts = super().validate(attrs)
        errors = {}
        extra_fields = set(self.initial_data.keys()) - set(self.fields.keys())
        
        for field in extra_fields:
            errors[field] = f"Field '{field}' is not allowed."
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return attrs
        
    def save(self, **kwargs):
        # Custom save logic for booking a class
        fitness_class_id = self.validated_data.pop('fitness_class_id')
        user = kwargs.get('user')

        if not user:
            raise serializers.ValidationError("User must be provided to book a class.")
        
        with transaction.atomic():
            try:
                # Lock the class row for update to prevent race conditions
                fitness_class = Classes.objects.select_for_update().get(id=fitness_class_id)
            except Classes.DoesNotExist:
                raise serializers.ValidationError("Class with this ID does not exists.")
            
            # Check if the class is available for booking
            if not fitness_class.is_available:
                raise serializers.ValidationError("This class is not available for booking.")
        
            # Prevent duplicate confirmed bookings for the same user and class
            if Booking.objects.filter(user=user, fitness_class=fitness_class, status='CONFIRMED').exists():
                raise serializers.ValidationError("You have already booked this class.")
            # Create the booking and decrement available slots
            booking = Booking.objects.create(
                user=user,
                fitness_class=fitness_class,
                status='CONFIRMED'
            )
            fitness_class.available_slots -= 1
            fitness_class.save()
            return booking 
        
        raise serializers.ValidationError("Failed to book the class due to a database error.")




