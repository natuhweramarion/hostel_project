from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('profile/', views.profile, name='profile'),
    path('about/', views.about_us, name='about'),
    path('contact/', views.contact_us, name='contact'),
]
