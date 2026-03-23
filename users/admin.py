from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Custom admin for CustomUser model"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_student', 'is_manager', 'department', 'level']
    list_filter = ['is_student', 'is_manager', 'is_staff', 'is_active', 'department', 'level', 'gender']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'student_id', 'phone_number']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {
            'fields': ('is_student', 'is_manager')
        }),
        ('Profile Information', {
            'fields': ('student_id', 'department', 'level', 'phone_number', 'date_of_birth', 'gender')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Information', {
            'fields': ('is_student', 'is_manager')
        }),
        ('Profile Information', {
            'fields': ('student_id', 'department', 'level', 'phone_number', 'date_of_birth', 'gender')
        }),
    )
