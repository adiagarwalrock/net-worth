"""
Admin configuration for User model.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for User model.
    """
    list_display = ['username', 'email', 'first_name', 'last_name', 'home_currency', 'email_verified', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'email_verified', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('home_currency', 'email_verified', 'phone_number'),
        }),
    )

    readonly_fields = ['date_joined', 'last_login']
