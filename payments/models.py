from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

class Payment(models.Model):
    """Payment records for hostel fees"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    reference_number = models.CharField(max_length=100, unique=True, help_text="Payment reference/transaction ID")
    date_paid = models.DateTimeField(auto_now_add=True)
    date_verified = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    academic_year = models.CharField(max_length=20, blank=True, null=True, help_text="e.g., 2023/2024")
    payment_method = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., Bank Transfer, Card, Cash")
    notes = models.TextField(blank=True, null=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_payments'
    )
    receipt = models.FileField(
        upload_to='payment_receipts/',
        blank=True,
        null=True,
        help_text="Proof of payment (image or PDF)"
    )

    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.status})"

    def delete(self, *args, **kwargs):
        """Delete uploaded receipt file from disk when the payment record is deleted."""
        if self.receipt:
            self.receipt.delete(save=False)
        super().delete(*args, **kwargs)

    class Meta:
        ordering = ['-date_paid']
        verbose_name = "Payment"
        verbose_name_plural = "Payments"


