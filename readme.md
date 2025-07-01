"""
🏃‍♀️ FITNESS STUDIO BOOKING API

## Project Overview:

This project is a Fitness Class Booking API built with Django + Django REST framework. It allows user to

1. Browse and book fitness classes
2. Cancel Booking
3. View Personal Statistics
- ADMIN's can:
4. Create, update, delete fitness classes
5. View platform-wide booking statistics

It uses JWT authenticatoin, enforces role-based access control, and include robust test coverage.

## Setup Instructions:

1. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Run migrations:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```
3. Create sample data:

   ```
   python manage.py seed_data
   ```

4. Run server:

   ```
   python manage.py runserver
   ```

5. Access the Admin Dashboard

   - Navigate to: http://localhost:8000/admin
   - Username: admin
   - Password: admin
   - Use this panel to view, edit and manage all models in the system.

6. Visit:
   - Swagger UI : http://localhost:8000/swagger/
   - ReDoc UI : http://localhost:8000/redoc/
   - Raw JSON : http://localhost:8000/swagger.json/

## Models

1. **Classes** : Represent a scheduled fitness session.

```
    class Classes(models.Model):
        name, class_type, instructor, duration_minutes,
        date_time, total_slots, available_slots
```

- **class_type** is restricte to choices: YOGA, ZUMBA, HIIT,
- **available_slots** is set automatically if not provided at creation.
- **is_upcoming** and **is_available** propertise define wheather a class can still be booked.

2. **Booking** : Represent a user's reservation for a class.

```
    class Booking(models.Model):
        user, fitness_class, status, booked_at, cancelled_at
```

- **status** : 'CONFIRMED' or 'CANCELLED'
- **Constraints** : A user cannot double-book the same class unless previous booking is cancelled.
- **.cancel()** is an atomic operation that safely updates the booking and restores slots.

## Serializers

1. **ClassesSerializer**

- Enforces:
  - **date_time** must be in future.
  - **total_slots** must be positive.
- **available_slots** is read-only.
- Extra fields in request are explicitly rejected.

2. **BookingSerializer**

- Accepts fitness_class_id as input.
- Automatically assosciates booking with request user.
- Handles:
  - Slot check (is_available).
  - Double-booking prevention.
  - Decreasing available_slots on booking.
- Uses **transaction.atomic()** to prevent race condition.

## Views

1. **Class Management**

- **ClassListView**
  - Any User can filter upcomming classes by type and date.
- **ClassCreateView, ClaseUpdateDeleteView**
  - Admin-only endpoints.
  - Protected with IsAdminUser permission.

2. **Booking Management**

- **BookingCreateView:**
  - User can book a class if:
    - Class is available.
    - Not already booked.
    - Slot is free.
- **BookingListView:**
  - Regular users see only their booking.
  - Admin can filter bookings by email and status.
- **BookingCancelView:**
  - User or Admin can cancel a booking.
  - Available slot is restored.

3. **Statistics Views**

- **StatisticsView (Admin Only)**
  - Give insights into the last 30 days.
    - total_classes
    - total_booking : sum of confirmed + cancelled
    - confirmed_booking, cancelled_booknig
    - popular_classes : top 5 by number of confirmed bookings
- **UserStatisticsView (Authenticated User Only)**
  - For the authenticated user:
    - Total confirmed booking
    - Cancelled booking
    - Count and details of upcomming bookings

## API Endpoints:

### Authentication:

- **POST** /api/auth/login/ - Get JWT token
- **POST** /api/auth/refresh/ - Refresh JWT token

### Classes:

- **GET** /api/classes/ - List upcoming classes
- **GET** /api/classes/?type=YOGA - Filter by class type
- **GET** /api/classes/?date=2024-01-15 - Filter by date

### Admin Class Management:

- **POST** /api/classes/create/ - Create new class (admin only)
- **PUT/DELETE** /api/classes/<id>/update/ - Update & Delete class (admin only)

### Bookings:

- **POST** /api/book/ - Book a class
- **GET** /api/bookings/ - Get user's bookings ( Authenticated User )
- **GET** /api/bookings/?email=user@example.com&status=confirmed - Get specific user's bookings (admin only)
- **POST** /api/bookings/<id>/cancel/ - Cancel booking

### Additional Endpoints:

- **GET** /api/stats/ - Get booking statistics (admin only)
- **GET** /api/stats/user/ - Get user profile and statistics

## Headers:

- Authorization: Bearer <jwt_token>
- X-Timezone: Asia/Kolkata (or any valid timezone)
- Content-Type: application/json

## Example Requests:

### 1. Login:

POST /api/auth/login/

```
{
    "username": "user1",
    "password": "user123"
}
```

Response:

```
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 2. Create Class (Admin):

POST /api/classes/create/
| Headers: Authorization: Bearer <admin_token>

```
{
    "name": "Morning Yoga",
    "class_type": "YOGA",
    "date_time": "16/08/2025 16:30",
    "instructor": "John Doe",
    "total_slots": 20,
    "duration_minutes": 60
}
```

### 3. Book Class:

POST /api/book/
| Headers: Authorization: Bearer <user_token>

```
{
    "fitness_class_id": 1
}
```

### 4. Get Classes with Timezone:

GET /api/classes/
| Headers: - **Authorization**: Bearer <token> - **X-Timezone**: America/New_York

Response:

```
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Morning Yoga",
            "class_type": "YOGA",
            "date_time": "16/08/2025 07:00", // Converted to EST
            "instructor": "John Doe",
            "total_slots": 20,
            "available_slots": 19,
            "duration_minutes": 60,
            "is_bookable": true
        }
    ]
}
```

### 5. Cancel Booking:

POST /api/bookings/1/cancel/
| Headers: Authorization: Bearer <user_token>

```
Response:
{
    "message": "Booking cancelled successfully"
}
```

### 6. Get User Statistics:

GET /api/stats/user/
| Headers: Authorization: Bearer <user_token>

Response:

```
{
    "user": {
        "id": 7,
        "username": "user1",
        "email": "user1@test.com",
        "first_name": "",
        "last_name": ""
    },
    "bookings": 2,
    "cancelled_bookings": 1,
    "upcoming_classes": 2,
    "upcoming_classes_details": [
            {
                "name": "Evening Zumba",
                "class_type": "ZUMBA",
                "duration_minutes": 45,
                "date_time": "2025-07-01T18:14:45.444390Z",
                "instructor": "Bob"
            },
            {
                "name": "Sunrise Yoga",
                "class_type": "YOGA",
                "duration_minutes": 60,
                "date_time": "2025-07-02T18:14:45.444390Z",
                "instructor": "Alice"
            }
        ]
}
```

## Features Implemented:

    ✅ JWT Authentication with refresh tokens
    ✅ Timezone management via request headers
    ✅ Admin CRUD operations for classes
    ✅ User booking with comprehensive validation
    ✅ One booking per user per class limitation
    ✅ Booking cancellation with automatic slot management
    ✅ Comprehensive error handling and logging
    ✅ Input validation and sanitization
    ✅ Unit tests with good coverage
    ✅ Proper database indexing for performance
    ✅ API documentation with examples
    ✅ Clean, modular, and well-documented code
    ✅ User profile and statistics
    ✅ Admin statistics dashboard
    ✅ Management commands for sample data
    ✅ Swagger API Documentation

## Error Handling Examples:

1. Overbooking Protection:

```
{
    "error": "No available slots for this class"
}
```

2. Duplicate Booking Prevention:

```
{
    "error": "User already has a booking for this class"
}
```

3. Past Class Booking:

```
{
    "error": "Class date/time must be in the future"
}
```

4. Invalid Timezone:

   - Automatically falls back to IST (Asia/Kolkata)

5. Authentication Errors:

```
{
    "detail": "Authentication credentials were not provided."
}
```

## Testing:

Run tests with: python manage.py test

This API provides a robust, production-ready booking system for fitness studios with all modern web API best practices implemented.
"""
