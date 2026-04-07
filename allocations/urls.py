from django.urls import path
from . import views

urlpatterns = [
    path('', views.allocation_list, name='allocation_list'),
    path('create/', views.create_allocation, name='create_allocation'),
    path('available-rooms/', views.available_rooms, name='available_rooms'),
    path('vacate/<int:allocation_id>/', views.vacate_allocation, name='vacate_allocation'),
    # Student hostel browsing & booking
    path('browse-hostels/', views.student_hostels, name='student_hostels'),
    path('browse-hostels/<int:hostel_id>/book/', views.create_booking_request, name='create_booking_request'),
    path('booking-requests/<int:request_id>/cancel/', views.cancel_booking_request, name='cancel_booking_request'),
    # Admin booking requests
    path('booking-requests/', views.booking_requests_admin, name='booking_requests_admin'),
    path('booking-requests/<int:request_id>/review/', views.review_booking_request, name='review_booking_request'),
]
