"""
Admin configuration for NetWorthSnapshot model.
"""
from django.contrib import admin
from .models import NetWorthSnapshot


@admin.register(NetWorthSnapshot)
class NetWorthSnapshotAdmin(admin.ModelAdmin):
    """
    Admin interface for NetWorthSnapshot model.
    """
    list_display = ['get_owner', 'net_worth', 'total_assets', 'total_liabilities', 'currency', 'debt_to_asset_ratio', 'snapshot_date', 'created_at']
    list_filter = ['currency', 'snapshot_date', 'created_at']
    search_fields = ['user__username', 'household__name']
    ordering = ['-snapshot_date']
    readonly_fields = ['created_at', 'debt_to_asset_ratio', 'total_assets', 'total_liabilities', 'net_worth', 'currency', 'snapshot_date']
    date_hierarchy = 'snapshot_date'

    fieldsets = (
        ('Owner', {
            'fields': ('user', 'household'),
        }),
        ('Financial Data', {
            'fields': ('total_assets', 'total_liabilities', 'net_worth', 'currency'),
        }),
        ('Calculated Metrics', {
            'fields': ('debt_to_asset_ratio',),
        }),
        ('Timestamps', {
            'fields': ('snapshot_date', 'created_at'),
            'classes': ('collapse',),
        }),
    )

    def get_owner(self, obj):
        """Display owner (user or household)."""
        if obj.user:
            return f"User: {obj.user.username}"
        elif obj.household:
            return f"Household: {obj.household.name}"
        return "N/A"
    get_owner.short_description = 'Owner'

    def debt_to_asset_ratio(self, obj):
        """Display debt-to-asset ratio as percentage."""
        if obj.pk and obj.total_assets is not None:
            return f"{obj.debt_to_asset_ratio:.2f}%"
        return "N/A"
    debt_to_asset_ratio.short_description = 'Debt/Asset Ratio'

    def get_queryset(self, request):
        """Filter queryset for non-superusers to only show their own snapshots."""
        qs = super().get_queryset(request).select_related('user', 'household', 'currency')
        if not request.user.is_superuser:
            # Show snapshots where user is the owner or part of the household
            from django.db.models import Q
            qs = qs.filter(
                Q(user=request.user) |
                Q(household__members__user=request.user)
            ).distinct()
        return qs

    def get_form(self, request, obj=None, **kwargs):
        """Customize form for non-superusers."""
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            # Limit user field to current user only
            if 'user' in form.base_fields:
                form.base_fields['user'].queryset = form.base_fields['user'].queryset.filter(id=request.user.id)
                form.base_fields['user'].initial = request.user
            # Limit household to ones user is part of
            if 'household' in form.base_fields:
                form.base_fields['household'].queryset = form.base_fields['household'].queryset.filter(
                    members__user=request.user
                )
        return form
