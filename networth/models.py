"""
Net Worth tracking and snapshot models.
"""
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class NetWorthSnapshot(models.Model):
    """
    Snapshot of a user's or household's net worth at a specific point in time.

    This model stores calculated net worth values periodically (daily) to enable
    historical tracking and trend analysis without recalculating from scratch.

    Attributes:
        user: User this snapshot belongs to (null for household snapshots)
        household: Household this snapshot belongs to (null for individual snapshots)
        total_assets: Total value of all assets at snapshot time
        total_liabilities: Total value of all liabilities at snapshot time
        net_worth: Calculated net worth (assets - liabilities)
        currency: Currency in which values are expressed
        snapshot_date: Date of this snapshot
        created_at: When this snapshot was created
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='networth_snapshots',
        null=True,
        blank=True,
        help_text="User this snapshot belongs to (null for household snapshots)"
    )
    household = models.ForeignKey(
        'households.Household',
        on_delete=models.CASCADE,
        related_name='networth_snapshots',
        null=True,
        blank=True,
        help_text="Household this snapshot belongs to (null for individual snapshots)"
    )
    total_assets = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total value of all assets at snapshot time (auto-calculated if not provided)"
    )
    total_liabilities = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total value of all liabilities at snapshot time (auto-calculated if not provided)"
    )
    net_worth = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Calculated net worth (assets - liabilities) (auto-calculated if not provided)"
    )
    currency = models.ForeignKey(
        'currencies.Currency',
        on_delete=models.PROTECT,
        related_name='networth_snapshots',
        null=True,
        blank=True,
        help_text="Currency in which values are expressed (auto-set to user's home currency if not provided)"
    )
    snapshot_date = models.DateField(
        db_index=True,
        null=True,
        blank=True,
        help_text="Date of this snapshot (defaults to today if not provided)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Net Worth Snapshot"
        verbose_name_plural = "Net Worth Snapshots"
        ordering = ['-snapshot_date']
        unique_together = [
            ['user', 'snapshot_date'],
            ['household', 'snapshot_date'],
        ]
        indexes = [
            models.Index(fields=['user', '-snapshot_date']),
            models.Index(fields=['household', '-snapshot_date']),
        ]

    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.currency.code} {self.net_worth} ({self.snapshot_date})"
        elif self.household:
            return f"{self.household.name} - {self.currency.code} {self.net_worth} ({self.snapshot_date})"
        return f"Snapshot - {self.currency.code} {self.net_worth} ({self.snapshot_date})"

    def clean(self):
        """
        Validate that snapshot has either user or household (but not both).
        """
        from django.core.exceptions import ValidationError
        if not self.user and not self.household:
            raise ValidationError("Snapshot must belong to either a user or a household.")
        if self.user and self.household:
            raise ValidationError("Snapshot cannot belong to both a user and a household.")

    def save(self, *args, **kwargs):
        """
        Override save to run validation and auto-calculate financial data.
        """
        # Run validation
        self.full_clean()

        # Auto-calculate financial data if not provided
        if self.user:
            # Individual snapshot
            if not self.currency:
                self.currency = self.user.get_home_currency()

            if self.total_assets is None:
                self.total_assets = self.user.get_total_assets()

            if self.total_liabilities is None:
                self.total_liabilities = self.user.get_total_liabilities()

        elif self.household:
            # Household snapshot
            if not self.currency:
                self.currency = self.household.created_by.get_home_currency()

            if self.total_assets is None or self.total_liabilities is None:
                # Calculate household totals
                from decimal import Decimal
                total_assets = Decimal('0.00')
                total_liabilities = Decimal('0.00')

                for member in self.household.members.select_related('user'):
                    total_assets += member.user.get_total_assets()
                    total_liabilities += member.user.get_total_liabilities()

                if self.total_assets is None:
                    self.total_assets = total_assets
                if self.total_liabilities is None:
                    self.total_liabilities = total_liabilities

        # Calculate net worth
        if self.net_worth is None:
            self.net_worth = self.total_assets - self.total_liabilities

        # Set snapshot_date to today if not provided
        if not self.snapshot_date:
            from django.utils import timezone
            self.snapshot_date = timezone.now().date()

        super().save(*args, **kwargs)

    @property
    def debt_to_asset_ratio(self):
        """
        Calculate debt-to-asset ratio.

        Returns:
            Decimal: Ratio of liabilities to assets (or 0 if no assets)
        """
        if self.total_assets and self.total_assets > 0:
            return (self.total_liabilities / self.total_assets) * 100
        return Decimal('0.00')

    @classmethod
    def get_latest_for_user(cls, user):
        """
        Get the most recent snapshot for a user.

        Args:
            user: User object

        Returns:
            NetWorthSnapshot or None
        """
        return cls.objects.filter(user=user).order_by('-snapshot_date').first()

    @classmethod
    def get_latest_for_household(cls, household):
        """
        Get the most recent snapshot for a household.

        Args:
            household: Household object

        Returns:
            NetWorthSnapshot or None
        """
        return cls.objects.filter(household=household).order_by('-snapshot_date').first()
