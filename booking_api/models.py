from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

class Classes(models.Model):
    CHOICES_CLASS = (
        ("YOGA", "Yoga"),
        ("ZUMBA", "Zumba"),
        ("HIIT", "HIIT")
    )
    name = models.CharField(max_length=100)
    class_type = models.CharField(max_length=100, choices=CHOICES_CLASS)
    instructor = models.CharField(max_length=100)
    duration_minutes = models.PositiveIntegerField()
    date_time = models.DateTimeField()
    total_slots = models.PositiveIntegerField()
    available_slots = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date_time']

    def save(self, *args, **kwargs):
        if not self.pk and self.available_slots is None:
            self.available_slots = self.total_slots
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} - {self.date_time}"
    
    @property
    def is_upcomming(self):
        return self.date_time > timezone.now()
    
    @property
    def is_available(self):
        return self.is_upcomming and self.available_slots > 0
    
class Booking(models.Model):
    CHOICES_STATUS = (
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    )    
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_bookings')
    fitness_class = models.ForeignKey(Classes, on_delete=models.CASCADE, related_name='class_bookings')
    status = models.CharField(max_length=20, choices=CHOICES_STATUS, default='CONFIRMED')
    booked_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'fitness_class'],
                condition=models.Q(status='CONFIRMED'),
                name='unique_active_user_class_booking'
            )
        ]
        indexes = [
            models.Index(fields=['booked_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.fitness_class.name}"
    
    def cancel(self):
        with transaction.atomic():
            # Ensure the booking is confirmed before cancelling
            if self.status != 'CONFIRMED':
                return False
            # Lock the Class, Update the booking status and available slots
            fitness_class = Classes.objects.select_for_update().get(pk=self.fitness_class.pk)
            self.status = 'CANCELLED'
            self.cancelled_at = timezone.now()
            fitness_class.available_slots += 1
            fitness_class.save()
            self.save()
        return True
    

