"""
Custom User model extending Django's AbstractUser.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model for net-worth tracking application.

    Extends Django's AbstractUser with additional fields for:
    - Home currency preference
    - Email verification
    - User profile information

    Attributes:
        email: User's email address (required, unique)
        home_currency: User's preferred currency for reporting
        email_verified: Whether the user has verified their email
        phone_number: Optional phone number
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    email = models.EmailField(
        unique=True,
        help_text="User's email address"
    )
    home_currency = models.ForeignKey(
        'currencies.Currency',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="User's preferred currency for reporting"
    )
    email_verified = models.BooleanField(
        default=False,
        help_text="Whether the user has verified their email"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="User's phone number"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Make email required
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-date_joined']

    def __str__(self):
        return self.username

    def get_home_currency(self):
        """
        Get user's home currency, fallback to USD if not set.

        Returns:
            Currency object
        """
        if self.home_currency:
            return self.home_currency

        # Import here to avoid circular imports
        from currencies.models import Currency
        usd, _ = Currency.objects.get_or_create(
            code='USD',
            defaults={
                'name': 'United States Dollar',
                'symbol': '$'
            }
        )
        return usd

    def get_total_assets(self):
        """
        Calculate total assets in home currency.

        Returns:
            Decimal: Total value of all assets in home currency
        """
        from assets.services import AssetService
        return AssetService.calculate_total_assets(self)

    def get_total_liabilities(self):
        """
        Calculate total liabilities in home currency.

        Returns:
            Decimal: Total value of all liabilities in home currency
        """
        from liabilities.services import LiabilityService
        return LiabilityService.calculate_total_liabilities(self)

    def get_net_worth(self):
        """
        Calculate net worth in home currency.

        Returns:
            Decimal: Net worth (assets - liabilities) in home currency
        """
        return self.get_total_assets() - self.get_total_liabilities()
