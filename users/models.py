from django.conf import settings
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


def create_notification(user, message, notif_type='general', link=''):
    """Helper — create a Notification record for a user."""
    Notification.objects.create(
        user=user,
        message=message,
        notif_type=notif_type,
        link=link,
    )


class Notification(models.Model):
    TYPE_CHOICES = [
        ('payment',    'Payment'),
        ('booking',    'Booking Request'),
        ('allocation', 'Allocation'),
        ('general',    'General'),
    ]

    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message    = models.TextField()
    notif_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='general')
    link       = models.CharField(max_length=200, blank=True)
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f'{self.user.username}: {self.message[:60]}'
