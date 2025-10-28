"""
Asset calculation and management services.
"""
from decimal import Decimal
from django.db.models import Sum


class AssetService:
    """
    Service layer for asset-related business logic.
    """

    @staticmethod
    def calculate_total_assets(user):
        """
        Calculate total value of all active assets for a user in their home currency.

        Args:
            user: User object

        Returns:
            Decimal: Total asset value in user's home currency
        """
        from assets.models import Asset

        home_currency = user.get_home_currency()
        total = Decimal('0.00')

        # Get all active assets for the user
        assets = Asset.objects.filter(user=user, is_active=True)

        for asset in assets:
            # Convert each asset to home currency
            converted_value = asset.get_value_in_currency(home_currency)
            total += converted_value

        return total

    @staticmethod
    def get_assets_by_type(user, asset_type=None):
        """
        Get assets for a user, optionally filtered by type.

        Args:
            user: User object
            asset_type: Optional asset type to filter by

        Returns:
            QuerySet: Asset objects
        """
        from assets.models import Asset

        queryset = Asset.objects.filter(user=user, is_active=True)

        if asset_type:
            queryset = queryset.filter(asset_type=asset_type)

        return queryset

    @staticmethod
    def get_asset_breakdown(user):
        """
        Get breakdown of assets by type in user's home currency.

        Args:
            user: User object

        Returns:
            dict: Dictionary with asset types as keys and total values as values
        """
        from assets.models import Asset

        home_currency = user.get_home_currency()
        breakdown = {}

        assets = Asset.objects.filter(user=user, is_active=True)

        for asset in assets:
            asset_type = asset.asset_type
            converted_value = asset.get_value_in_currency(home_currency)

            if asset_type in breakdown:
                breakdown[asset_type] += converted_value
            else:
                breakdown[asset_type] = converted_value

        return breakdown
