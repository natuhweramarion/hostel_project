from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('allocations/', views.allocation_report, name='allocation_report'),
    path('payments/', views.payment_report, name='payment_report'),
    path('occupancy/', views.hostel_occupancy_report, name='hostel_occupancy_report'),
]
