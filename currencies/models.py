"""
Currency and Exchange Rate models for multi-currency support.
"""
from django.db import models
from django.utils import timezone


class Currency(models.Model):
    """
    Represents a currency (USD, EUR, INR, etc.).

    Attributes:
        code: ISO 4217 currency code (e.g., USD, EUR)
        name: Full name of the currency
        symbol: Currency symbol (e.g., $, €, ₹)
        is_active: Whether this currency is currently supported
    """
    code = models.CharField(
        max_length=3,
        unique=True,
        db_index=True,
        help_text="ISO 4217 currency code (e.g., USD, EUR, INR)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Full name of the currency"
    )
    symbol = models.CharField(
        max_length=10,
        help_text="Currency symbol (e.g., $, €, ₹)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this currency is currently supported"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class ExchangeRate(models.Model):
    """
    Stores historical exchange rates between currencies.

    Attributes:
        from_currency: Source currency
        to_currency: Target currency
        rate: Exchange rate (1 from_currency = rate * to_currency)
        date: Date for which this rate is valid
        source: API source that provided this rate
    """
    from_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='rates_from',
        help_text="Source currency"
    )
    to_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='rates_to',
        help_text="Target currency"
    )
    rate = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        help_text="Exchange rate (1 from_currency = rate * to_currency)"
    )
    date = models.DateField(
        default=timezone.now,
        db_index=True,
        help_text="Date for which this rate is valid"
    )
    source = models.CharField(
        max_length=100,
        default='exchangerate-api',
        help_text="API source that provided this rate"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Exchange Rate"
        verbose_name_plural = "Exchange Rates"
        ordering = ['-date', 'from_currency', 'to_currency']
        unique_together = ['from_currency', 'to_currency', 'date']
        indexes = [
            models.Index(fields=['from_currency', 'to_currency', '-date']),
        ]

    def __str__(self):
        return f"{self.from_currency.code}/{self.to_currency.code} = {self.rate} ({self.date})"

    @staticmethod
    def get_latest_rate(from_currency, to_currency):
        """
        Get the most recent exchange rate between two currencies.

        Args:
            from_currency: Source Currency object
            to_currency: Target Currency object

        Returns:
            ExchangeRate object or None if not found
        """
        return ExchangeRate.objects.filter(
            from_currency=from_currency,
            to_currency=to_currency
        ).order_by('-date').first()

    @staticmethod
    def get_rate_for_date(from_currency, to_currency, date):
        """
        Get the exchange rate for a specific date.

        Args:
            from_currency: Source Currency object
            to_currency: Target Currency object
            date: Date object

        Returns:
            ExchangeRate object or None if not found
        """
        return ExchangeRate.objects.filter(
            from_currency=from_currency,
            to_currency=to_currency,
            date=date
        ).first()
