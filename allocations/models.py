from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from hostels.models import Room, Hostel

class Allocation(models.Model):
    """Room allocation for students"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('left', 'Left'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='allocations')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='allocations')
    date_allocated = models.DateTimeField(auto_now_add=True)
    date_left = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    academic_year = models.CharField(max_length=20, blank=True, null=True, help_text="e.g., 2023/2024")
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.room} ({self.status})"

    def clean(self):
        """Validate allocation before saving"""
        if self.status == 'active':
            # --- Capacity check ---
            if self.pk:
                active_allocations = Allocation.objects.filter(
                    room=self.room,
                    status='active'
                ).exclude(pk=self.pk).count()
            else:
                active_allocations = Allocation.objects.filter(
                    room=self.room,
                    status='active'
                ).count()

            if active_allocations >= self.room.capacity:
                raise ValidationError(
                    f"Room {self.room.room_number} is full. Capacity: {self.room.capacity}"
                )

            # --- Duplicate active allocation check ---
            if self.pk:
                existing = Allocation.objects.filter(
                    user=self.user,
                    status='active'
                ).exclude(pk=self.pk).exists()
            else:
                existing = Allocation.objects.filter(
                    user=self.user,
                    status='active'
                ).exists()

            if existing:
                raise ValidationError(
                    f"User {self.user.username} already has an active allocation."
                )

            # --- Gender-matching check ---
            hostel_gender = self.room.block.hostel.gender
            student_gender = self.user.gender
            if hostel_gender != 'Mixed' and student_gender and hostel_gender != student_gender:
                raise ValidationError(
                    f"This hostel is {hostel_gender}-only. "
                    f"{self.user.get_full_name()} is registered as {student_gender}."
                )

    def save(self, *args, **kwargs):
        """Override save to validate"""
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Override delete"""
        super().delete(*args, **kwargs)

    class Meta:
        ordering = ['-date_allocated']
        verbose_name = "Allocation"
        verbose_name_plural = "Allocations"
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(status='active'),
                name='unique_active_allocation_per_student'
            )
        ]


class BookingRequest(models.Model):
    """A student's request to be allocated to a specific hostel."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='booking_requests'
    )
    preferred_hostel = models.ForeignKey(
        Hostel, on_delete=models.CASCADE, related_name='booking_requests'
    )
    academic_year = models.CharField(max_length=20, help_text="e.g. 2024/2025")
    message = models.TextField(blank=True, null=True, help_text="Any additional notes for the hostel office")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_booking_requests'
    )
    admin_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.username} → {self.preferred_hostel.name} ({self.status})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Booking Request"
        verbose_name_plural = "Booking Requests"
