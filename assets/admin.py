"""
Admin configuration for Asset models.
"""
from django.contrib import admin
from .models import Asset, AssetHistory


class AssetHistoryInline(admin.TabularInline):
    """
    Inline admin for asset history.
    """
    model = AssetHistory
    extra = 0
    readonly_fields = ['recorded_at']
    fields = ['value', 'currency', 'source', 'recorded_at']
    can_delete = False
    ordering = ['-recorded_at']

    def has_add_permission(self, request, obj=None):
        """Disable manual addition of history records."""
        return False


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """
    Admin interface for Asset model.
    """
    list_display = ['name', 'user', 'asset_type', 'value', 'currency', 'institution', 'is_active', 'last_valued_at']
    list_filter = ['asset_type', 'currency', 'is_active', 'created_at']
    search_fields = ['name', 'user__username', 'institution', 'notes']
    ordering = ['-updated_at']
    readonly_fields = ['created_at', 'updated_at', 'last_valued_at']
    inlines = [AssetHistoryInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Asset Information', {
            'fields': ('user', 'name', 'asset_type', 'value', 'currency'),
        }),
        ('Additional Details', {
            'fields': ('institution', 'account_number', 'notes'),
        }),
        ('Status', {
            'fields': ('is_active',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_valued_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        """Filter queryset for non-superusers to only show their own assets."""
        qs = super().get_queryset(request).select_related('user', 'currency')
        if not request.user.is_superuser:
            qs = qs.filter(user=request.user)
        return qs

    def get_form(self, request, obj=None, **kwargs):
        """Customize form to hide user field for non-superusers."""
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            # Hide user field for non-superusers
            if 'user' in form.base_fields:
                form.base_fields['user'].widget = admin.widgets.HiddenInput()
        return form

    def save_model(self, request, obj, form, change):
        """Auto-set user to current logged-in user for non-superusers."""
        if not request.user.is_superuser:
            obj.user = request.user
        super().save_model(request, obj, form, change)


@admin.register(AssetHistory)
class AssetHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for AssetHistory model.
    """
    list_display = ['asset', 'value', 'currency', 'source', 'recorded_at']
    list_filter = ['source', 'currency', 'recorded_at']
    search_fields = ['asset__name', 'asset__user__username']
    ordering = ['-recorded_at']
    readonly_fields = ['recorded_at']
    date_hierarchy = 'recorded_at'

    fieldsets = (
        ('History Information', {
            'fields': ('asset', 'value', 'currency', 'source'),
        }),
        ('Timestamp', {
            'fields': ('recorded_at',),
        }),
    )

    def has_add_permission(self, request):
        """Disable manual addition of history records."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make history records read-only."""
        return False
