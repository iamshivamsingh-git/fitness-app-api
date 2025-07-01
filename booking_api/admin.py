from django.contrib import admin
from .models import Classes, Booking

@admin.register(Classes)
class ClassAdmin(admin.ModelAdmin):
    list_display = ["name", "class_type", "date_time", "instructor", "available_slots", "total_slots"]
    list_filter = ["class_type", "date_time", "instructor"]
    search_fields = ["name", "instructor"]
    readonly_fields = ["created_at", "updated_at"]

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["user", "fitness_class", "status", "booked_at"]
    list_filter = ["status", "booked_at", "fitness_class__class_type"]
    search_fields = ["user__email", "fitness_class__name"]
    readonly_fields = ["booked_at", "cancelled_at"]