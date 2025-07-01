from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Authentication
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Classes
    path('classes/', views.ClassListView.as_view(), name='class-list'),
    path('classes/create/', views.ClassCreateView.as_view(), name='class-create'),
    path('classes/<int:pk>/update/', views.ClassUpdateDeleteView.as_view(), name='class-detail'),

    # Booking
    path('book/', views.BookingCreateView.as_view(), name='booking-create'),
    path('bookings/', views.BookingListView.as_view(), name='booking-list'),
    path('bookings/<int:pk>/cancel/', views.BookingCancelView.as_view(), name='booking-cancel'),

    # Statistics
    path('stats/', views.StatisticsView.as_view(), name='statistics'),
    path('stats/user/', views.UserStatisticsView.as_view(), name='user-statistics'),
]