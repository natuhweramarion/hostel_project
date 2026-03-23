from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """Extended user model with student and manager roles"""
    
    # Role fields
    is_student = models.BooleanField(default=False, help_text="Designates if user is a student")
    is_manager = models.BooleanField(default=False, help_text="Designates if user is a hostel manager/admin")
    
    # Profile fields
    department = models.CharField(max_length=100, blank=True, null=True)
    level = models.CharField(max_length=20, blank=True, null=True, help_text="e.g., 100, 200, 300, 400")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Additional fields
    student_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')], blank=True, null=True)
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True, help_text="Profile photo")
    
    def __str__(self):
        return f"{self.username} - {self.get_full_name()}"
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
