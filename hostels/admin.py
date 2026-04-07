from django.contrib import admin
from .models import Hostel, Block, Room

@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    """Admin for Hostel model"""
    list_display = ['name', 'location', 'gender', 'price_per_semester', 'has_image', 'created_at']
    list_filter = ['gender', 'created_at']
    search_fields = ['name', 'location', 'description']
    ordering = ['name']

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = 'Banner'

@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    """Admin for Block model"""
    list_display = ['name', 'hostel', 'capacity', 'created_at']
    list_filter = ['hostel', 'created_at']
    search_fields = ['name', 'hostel__name', 'description']
    ordering = ['hostel', 'name']

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Admin for Room model"""
    list_display = ['room_number', 'block', 'room_type', 'capacity', 'price_per_semester', 'get_is_full', 'occupied_beds', 'available_beds']
    list_filter = ['block__hostel', 'block', 'room_type', 'created_at']
    search_fields = ['room_number', 'block__name', 'block__hostel__name']
    ordering = ['block', 'room_number']

    def get_is_full(self, obj):
        return obj.is_full
    get_is_full.boolean = True
    get_is_full.short_description = 'Full?'
    
    def occupied_beds(self, obj):
        return obj.occupied_beds()
    occupied_beds.short_description = 'Occupied Beds'
    
    def available_beds(self, obj):
        return obj.available_beds()
    available_beds.short_description = 'Available Beds'
