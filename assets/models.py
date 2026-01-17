"""
Asset tracking models for various asset types.
"""
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from common.enums import AssetType, HistorySource


class Asset(models.Model):
    """
    Represents a financial asset owned by a user.

    Supports multiple asset types:
    - Cash & Bank Accounts
    - Investment Portfolios
    - Real Estate
    - Vehicles
    - Other Assets

    Attributes:
        user: Owner of this asset
        name: Asset name/description
        asset_type: Category of asset
        value: Current value
        currency: Currency in which value is denominated
        institution: Bank/brokerage/etc (optional)
        account_number: Last 4 digits or masked account number (optional)
        notes: Additional notes
        is_active: Soft delete flag
        created_at: Creation timestamp
        updated_at: Last update timestamp
        last_valued_at: When value was last updated
    """
    # Asset Type Choices (using centralized enums)
    CASH = AssetType.CASH
    INVESTMENT = AssetType.INVESTMENT
    REAL_ESTATE = AssetType.REAL_ESTATE
    VEHICLE = AssetType.VEHICLE
    PRECIOUS_METALS = AssetType.PRECIOUS_METALS
    CRYPTOCURRENCY = AssetType.CRYPTOCURRENCY
    OTHER = AssetType.OTHER

    ASSET_TYPE_CHOICES = AssetType.choices

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assets',
        help_text="Owner of this asset"
    )
    name = models.CharField(
        max_length=200,
        help_text="Asset name or description"
    )
    asset_type = models.CharField(
        max_length=20,
        choices=ASSET_TYPE_CHOICES,
        help_text="Category of asset"
    )
    value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Current value of the asset"
    )
    currency = models.ForeignKey(
        'currencies.Currency',
        on_delete=models.PROTECT,
        related_name='assets',
        help_text="Currency in which value is denominated"
    )
    institution = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Bank, brokerage, or institution name"
    )
    account_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Masked account number (e.g., ****1234)"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about this asset"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this asset is currently active (soft delete)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_valued_at = models.DateTimeField(
        auto_now=True,
        help_text="When value was last updated"
    )

    class Meta:
        verbose_name = "Asset"
        verbose_name_plural = "Assets"
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'asset_type', 'is_active']),
            models.Index(fields=['user', 'is_active', '-updated_at']),
            models.Index(fields=['currency', 'is_active'], name='asset_currency_active_idx'),
        ]

    def __str__(self):
        return f"{self.name} - {self.currency.code} {self.value}"

    def get_value_in_currency(self, target_currency):
        """
        Convert asset value to target currency.

        Args:
            target_currency: Currency object to convert to

        Returns:
            Decimal: Value in target currency
        """
        if self.currency == target_currency:
            return self.value

        from currencies.services import CurrencyService
        return CurrencyService.convert(
            amount=self.value,
            from_currency=self.currency,
            to_currency=target_currency
        )

    def save(self, *args, **kwargs):
        """
        Override save to create history record on value change.

        To skip automatic history creation (e.g., when manually creating with custom source),
        pass skip_history=True in kwargs.
        """
        skip_history = kwargs.pop('skip_history', False)

        is_new = self.pk is None
        old_value = None

        if not is_new:
            old_value = Asset.objects.filter(pk=self.pk).values_list('value', flat=True).first()

        super().save(*args, **kwargs)

        # Create history record if value changed or new asset (unless skipped)
        if not skip_history and (is_new or (old_value is not None and old_value != self.value)):
            AssetHistory.objects.create(
                asset=self,
                value=self.value,
                currency=self.currency,
                source=AssetHistory.MANUAL
            )


class AssetHistory(models.Model):
    """
    Historical record of asset values over time.

    Attributes:
        asset: Asset this history belongs to
        value: Value at this point in time
        currency: Currency of the value
        recorded_at: Timestamp of this record
        source: How this value was recorded
    """
    # History Source Choices (using centralized enums)
    MANUAL = HistorySource.MANUAL
    STATEMENT_UPLOAD = HistorySource.STATEMENT_UPLOAD
    API_SYNC = HistorySource.API_SYNC

    SOURCE_CHOICES = HistorySource.choices

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='history',
        help_text="Asset this history belongs to"
    )
    value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Value at this point in time"
    )
    currency = models.ForeignKey(
        'currencies.Currency',
        on_delete=models.PROTECT,
        related_name='asset_history',
        help_text="Currency of the value"
    )
    recorded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp of this record"
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default=MANUAL,
        help_text="How this value was recorded"
    )

    class Meta:
        verbose_name = "Asset History"
        verbose_name_plural = "Asset Histories"
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['asset', '-recorded_at']),
            models.Index(fields=['asset', 'source'], name='asset_history_source_idx'),
        ]

    def __str__(self):
        return f"{self.asset.name} - {self.currency.code} {self.value} at {self.recorded_at}"
