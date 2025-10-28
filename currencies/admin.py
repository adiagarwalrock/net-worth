"""
Admin configuration for Currency and ExchangeRate models.
"""
from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from .models import Currency, ExchangeRate
from .services import CurrencyService


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    """
    Admin interface for Currency model.
    """
    list_display = ['code', 'name', 'symbol', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name']
    ordering = ['code']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Currency Information', {
            'fields': ('code', 'name', 'symbol', 'is_active'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def changelist_view(self, request, extra_context=None):
        """Add custom context to changelist view."""
        extra_context = extra_context or {}
        extra_context['title'] = 'Currencies (Auto-fetched from ExchangeRate-API)'
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    """
    Admin interface for ExchangeRate model.

    Exchange rates are automatically fetched from ExchangeRate-API daily at 9 AM UTC.
    You can manually refresh rates using the "Update Exchange Rates" action below.
    """
    list_display = ['from_currency', 'to_currency', 'rate', 'date', 'source', 'created_at']
    list_filter = ['from_currency', 'to_currency', 'date', 'source']
    search_fields = ['from_currency__code', 'to_currency__code']
    ordering = ['-date', 'from_currency', 'to_currency']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'
    actions = ['update_exchange_rates_now']

    fieldsets = (
        ('Exchange Rate Information', {
            'fields': ('from_currency', 'to_currency', 'rate', 'date', 'source'),
            'description': 'Exchange rates are auto-fetched daily. Manual entry is not needed.'
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    def changelist_view(self, request, extra_context=None):
        """Add custom context and button to changelist view."""
        extra_context = extra_context or {}
        extra_context['title'] = 'Exchange Rates (Auto-updated daily at 9 AM UTC)'
        extra_context['subtitle'] = format_html(
            '<div style="background: #e7f7ff; padding: 10px; border-radius: 5px; margin: 10px 0;">'
            '<strong>ℹ️ Info:</strong> Exchange rates are automatically fetched from '
            '<a href="https://www.exchangerate-api.com/docs/free" target="_blank">ExchangeRate-API</a> '
            'every day at 9:00 AM UTC. Use the action below to manually update rates now.'
            '</div>'
        )
        return super().changelist_view(request, extra_context=extra_context)

    def update_exchange_rates_now(self, request, queryset):
        """
        Admin action to manually update exchange rates from API.
        """
        try:
            success, message, rates_updated = CurrencyService.update_exchange_rates_for_currency('USD')

            if success:
                self.message_user(
                    request,
                    f"✅ Successfully updated {rates_updated} exchange rates from API.",
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    f"❌ Failed to update exchange rates: {message}",
                    messages.ERROR
                )
        except Exception as e:
            self.message_user(
                request,
                f"❌ Error updating exchange rates: {str(e)}",
                messages.ERROR
            )

    update_exchange_rates_now.short_description = "🔄 Update Exchange Rates from API (USD base)"

    def has_add_permission(self, request):
        """
        Disable manual addition of exchange rates.
        Rates should be fetched automatically or via the update action.
        """
        return False
