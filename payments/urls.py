from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('create/', views.create_payment, name='create_payment'),
    path('verify/<int:payment_id>/', views.verify_payment, name='verify_payment'),
    path('receipt/<int:payment_id>/', views.payment_receipt, name='payment_receipt'),
]
