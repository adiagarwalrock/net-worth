"""ABOUTME: Net worth calculation services for users and households.
ABOUTME: Aggregates assets and liabilities across members and currencies.
"""
from decimal import Decimal
from collections import defaultdict
from assets.models import Asset
from assets.services import AssetService
from liabilities.models import Liability
from liabilities.services import LiabilityService


class NetWorthService:
    """
    Service layer for net worth calculation business logic.
    """

    @staticmethod
    def calculate_household_net_worth(household):
        """
        Calculate combined net worth for all household members.

        Optimized to fetch all assets/liabilities in bulk queries instead of
        per-user queries, reducing O(N×M) to O(2) database queries.

        Inputs:
            household: Household object

        Outputs:
            Decimal: Total household net worth in creator's home currency
        """
        # Use the household creator's home currency as the common currency
        target_currency = household.created_by.get_home_currency()
        total_net_worth = Decimal('0.00')

        # Get all members in the household
        members = household.members.select_related('user', 'user__home_currency').all()
        user_ids = [member.user.id for member in members]

        # Bulk fetch all assets for all household members (single query)
        all_assets = Asset.objects.filter(
            user_id__in=user_ids,
            is_active=True
        ).select_related('currency', 'user')

        # Bulk fetch all liabilities for all household members (single query)
        all_liabilities = Liability.objects.filter(
            user_id__in=user_ids,
            is_active=True
        ).select_related('currency', 'user')

        # Group assets by user
        assets_by_user = defaultdict(list)
        for asset in all_assets:
            assets_by_user[asset.user_id].append(asset)

        # Group liabilities by user
        liabilities_by_user = defaultdict(list)
        for liability in all_liabilities:
            liabilities_by_user[liability.user_id].append(liability)

        # Calculate net worth for each member
        for member in members:
            user = member.user
            user_currency = user.get_home_currency()

            # Sum assets for this user
            user_assets = Decimal('0.00')
            for asset in assets_by_user[user.id]:
                value_in_user_currency = asset.get_value_in_currency(user_currency)
                user_assets += value_in_user_currency

            # Sum liabilities for this user
            user_liabilities = Decimal('0.00')
            for liability in liabilities_by_user[user.id]:
                balance_in_user_currency = liability.get_balance_in_currency(user_currency)
                user_liabilities += balance_in_user_currency

            # Convert to target currency if needed
            if user_currency != target_currency:
                from currencies.services import CurrencyService
                user_assets = CurrencyService.convert(
                    amount=user_assets,
                    from_currency=user_currency,
                    to_currency=target_currency
                )
                user_liabilities = CurrencyService.convert(
                    amount=user_liabilities,
                    from_currency=user_currency,
                    to_currency=target_currency
                )

            # Add to household total
            user_net_worth = user_assets - user_liabilities
            total_net_worth += user_net_worth

        return total_net_worth

    @staticmethod
    def calculate_user_net_worth(user):
        """
        Calculate net worth for a single user.

        Inputs:
            user: User object

        Outputs:
            Decimal: User's net worth in their home currency
        """
        total_assets = AssetService.calculate_total_assets(user)
        total_liabilities = LiabilityService.calculate_total_liabilities(user)
        return total_assets - total_liabilities

    @staticmethod
    def get_household_breakdown(household):
        """
        Get per-member breakdown of household net worth.

        Optimized to fetch all assets/liabilities in bulk queries instead of
        per-user queries, reducing O(N×M) to O(2) database queries.

        Inputs:
            household: Household object

        Outputs:
            list: List of dicts with member info and net worth
                [{'user': User, 'assets': Decimal, 'liabilities': Decimal, 'net_worth': Decimal}, ...]
        """
        target_currency = household.created_by.get_home_currency()
        breakdown = []

        # Get all members in the household
        members = household.members.select_related('user', 'user__home_currency').all()
        user_ids = [member.user.id for member in members]

        # Bulk fetch all assets for all household members (single query)
        all_assets = Asset.objects.filter(
            user_id__in=user_ids,
            is_active=True
        ).select_related('currency', 'user')

        # Bulk fetch all liabilities for all household members (single query)
        all_liabilities = Liability.objects.filter(
            user_id__in=user_ids,
            is_active=True
        ).select_related('currency', 'user')

        # Group assets by user
        assets_by_user = defaultdict(list)
        for asset in all_assets:
            assets_by_user[asset.user_id].append(asset)

        # Group liabilities by user
        liabilities_by_user = defaultdict(list)
        for liability in all_liabilities:
            liabilities_by_user[liability.user_id].append(liability)

        # Build breakdown for each member
        for member in members:
            user = member.user
            user_currency = user.get_home_currency()

            # Sum assets for this user
            user_assets = Decimal('0.00')
            for asset in assets_by_user[user.id]:
                value_in_user_currency = asset.get_value_in_currency(user_currency)
                user_assets += value_in_user_currency

            # Sum liabilities for this user
            user_liabilities = Decimal('0.00')
            for liability in liabilities_by_user[user.id]:
                balance_in_user_currency = liability.get_balance_in_currency(user_currency)
                user_liabilities += balance_in_user_currency

            # Convert to target currency if needed
            if user_currency != target_currency:
                from currencies.services import CurrencyService
                user_assets = CurrencyService.convert(
                    amount=user_assets,
                    from_currency=user_currency,
                    to_currency=target_currency
                )
                user_liabilities = CurrencyService.convert(
                    amount=user_liabilities,
                    from_currency=user_currency,
                    to_currency=target_currency
                )

            breakdown.append({
                'user': user,
                'assets': user_assets,
                'liabilities': user_liabilities,
                'net_worth': user_assets - user_liabilities,
            })

        return breakdown
