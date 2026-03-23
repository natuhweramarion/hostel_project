from django.contrib import admin
from .models import Allocation, BookingRequest


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ['student', 'preferred_hostel', 'academic_year', 'status', 'created_at']
    list_filter = ['status', 'preferred_hostel', 'created_at']
    search_fields = ['student__username', 'student__first_name', 'student__last_name', 'preferred_hostel__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at']

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing existing object
            return self.readonly_fields + ['student', 'preferred_hostel']
        return self.readonly_fields


@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    """Admin for Allocation model"""
    list_display = ['user', 'room', 'status', 'date_allocated', 'academic_year']
    list_filter = ['status', 'date_allocated', 'academic_year', 'room__block__hostel']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'room__room_number', 'room__block__name']
    ordering = ['-date_allocated']
    date_hierarchy = 'date_allocated'
    
    fieldsets = (
        ('Allocation Details', {
            'fields': ('user', 'room', 'status', 'academic_year')
        }),
        ('Dates', {
            'fields': ('date_allocated', 'date_left')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
    )
    
    readonly_fields = ['date_allocated']
