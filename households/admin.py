"""
Admin configuration for Household models.
"""
from django.contrib import admin
from .models import Household, HouseholdMember, HouseholdInvitation


class HouseholdMemberInline(admin.TabularInline):
    """
    Inline admin for household members.
    """
    model = HouseholdMember
    extra = 0
    readonly_fields = ['joined_at']
    fields = ['user', 'role', 'can_view_details', 'joined_at']


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    """
    Admin interface for Household model.
    """
    list_display = ['name', 'created_by', 'get_members_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'created_by__username', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'get_members_count']
    inlines = [HouseholdMemberInline]

    fieldsets = (
        ('Household Information', {
            'fields': ('name', 'created_by', 'description'),
        }),
        ('Statistics', {
            'fields': ('get_members_count',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_members_count(self, obj):
        """Display member count."""
        return obj.get_members_count()
    get_members_count.short_description = 'Members Count'


@admin.register(HouseholdMember)
class HouseholdMemberAdmin(admin.ModelAdmin):
    """
    Admin interface for HouseholdMember model.
    """
    list_display = ['user', 'household', 'role', 'can_view_details', 'joined_at']
    list_filter = ['role', 'can_view_details', 'joined_at']
    search_fields = ['user__username', 'household__name']
    ordering = ['-joined_at']
    readonly_fields = ['joined_at']

    fieldsets = (
        ('Membership Information', {
            'fields': ('household', 'user', 'role', 'can_view_details'),
        }),
        ('Timestamp', {
            'fields': ('joined_at',),
            'classes': ('collapse',),
        }),
    )


@admin.register(HouseholdInvitation)
class HouseholdInvitationAdmin(admin.ModelAdmin):
    """
    Admin interface for HouseholdInvitation model.
    """
    list_display = ['email', 'household', 'invited_by', 'role', 'status', 'created_at', 'expires_at']
    list_filter = ['status', 'role', 'created_at']
    search_fields = ['email', 'household__name', 'invited_by__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'token']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Invitation Information', {
            'fields': ('household', 'email', 'invited_by', 'role'),
        }),
        ('Status', {
            'fields': ('status', 'token', 'expires_at'),
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
