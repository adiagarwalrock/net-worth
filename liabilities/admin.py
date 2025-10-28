"""
Admin configuration for Liability models.
"""
from django.contrib import admin
from .models import Liability, LiabilityHistory


class LiabilityHistoryInline(admin.TabularInline):
    """
    Inline admin for liability history.
    """
    model = LiabilityHistory
    extra = 0
    readonly_fields = ['recorded_at']
    fields = ['balance', 'currency', 'source', 'recorded_at']
    can_delete = False
    ordering = ['-recorded_at']

    def has_add_permission(self, request, obj=None):
        """Disable manual addition of history records."""
        return False


@admin.register(Liability)
class LiabilityAdmin(admin.ModelAdmin):
    """
    Admin interface for Liability model.
    """
    list_display = ['name', 'user', 'liability_type', 'balance', 'currency', 'creditor', 'interest_rate', 'is_active', 'last_valued_at']
    list_filter = ['liability_type', 'currency', 'is_active', 'created_at']
    search_fields = ['name', 'user__username', 'creditor', 'notes']
    ordering = ['-updated_at']
    readonly_fields = ['created_at', 'updated_at', 'last_valued_at']
    inlines = [LiabilityHistoryInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Liability Information', {
            'fields': ('user', 'name', 'liability_type', 'balance', 'currency'),
        }),
        ('Creditor Details', {
            'fields': ('creditor', 'account_number'),
        }),
        ('Loan Details', {
            'fields': ('interest_rate', 'monthly_payment', 'credit_limit', 'payment_due_date'),
        }),
        ('Additional Information', {
            'fields': ('notes',),
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
        """Optimize query with select_related."""
        return super().get_queryset(request).select_related('user', 'currency')


@admin.register(LiabilityHistory)
class LiabilityHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for LiabilityHistory model.
    """
    list_display = ['liability', 'balance', 'currency', 'source', 'recorded_at']
    list_filter = ['source', 'currency', 'recorded_at']
    search_fields = ['liability__name', 'liability__user__username']
    ordering = ['-recorded_at']
    readonly_fields = ['recorded_at']
    date_hierarchy = 'recorded_at'

    fieldsets = (
        ('History Information', {
            'fields': ('liability', 'balance', 'currency', 'source'),
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
