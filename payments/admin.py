from django.contrib import admin
from django.utils import timezone
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin for Payment model"""
    list_display = ['user', 'amount', 'reference_number', 'status', 'date_paid', 'verified_by']
    list_filter = ['status', 'date_paid', 'academic_year', 'payment_method']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'reference_number']
    ordering = ['-date_paid']
    date_hierarchy = 'date_paid'
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('user', 'amount', 'reference_number', 'payment_method', 'academic_year')
        }),
        ('Status', {
            'fields': ('status', 'verified_by', 'date_verified')
        }),
        ('Additional Information', {
            'fields': ('notes', 'receipt')
        }),
    )
    
    readonly_fields = ['date_paid']
    
    actions = ['mark_as_verified', 'mark_as_pending']
    
    def mark_as_verified(self, request, queryset):
        """Mark selected payments as verified"""
        updated = queryset.update(
            status='verified',
            verified_by=request.user,
            date_verified=timezone.now()
        )
        self.message_user(request, f'{updated} payment(s) marked as verified.')
    mark_as_verified.short_description = 'Mark selected payments as verified'
    
    def mark_as_pending(self, request, queryset):
        """Mark selected payments as pending"""
        updated = queryset.update(status='pending', verified_by=None, date_verified=None)
        self.message_user(request, f'{updated} payment(s) marked as pending.')
    mark_as_pending.short_description = 'Mark selected payments as pending'

