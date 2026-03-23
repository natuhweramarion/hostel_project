from django.urls import path
from . import views

urlpatterns = [
    path('browse/', views.public_hostels, name='public_hostels'),
    path('', views.hostel_list, name='hostel_list'),
    path('create/', views.hostel_create, name='hostel_create'),
    path('<int:hostel_id>/', views.hostel_detail, name='hostel_detail'),
    path('<int:hostel_id>/edit/', views.hostel_edit, name='hostel_edit'),
    path('<int:hostel_id>/block/add/', views.block_create, name='block_create'),
    path('<int:hostel_id>/block/<int:block_id>/room/add/', views.room_create, name='room_create'),
]
