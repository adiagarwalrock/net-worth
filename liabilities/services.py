"""
Liability calculation and management services.
"""
from decimal import Decimal
from django.db.models import Sum


class LiabilityService:
    """
    Service layer for liability-related business logic.
    """

    @staticmethod
    def calculate_total_liabilities(user):
        """
        Calculate total balance of all active liabilities for a user in their home currency.

        Args:
            user: User object

        Returns:
            Decimal: Total liability balance in user's home currency
        """
        from liabilities.models import Liability

        home_currency = user.get_home_currency()
        total = Decimal('0.00')

        # Get all active liabilities for the user
        liabilities = Liability.objects.filter(user=user, is_active=True)

        for liability in liabilities:
            # Convert each liability to home currency
            converted_balance = liability.get_balance_in_currency(home_currency)
            total += converted_balance

        return total

    @staticmethod
    def get_liabilities_by_type(user, liability_type=None):
        """
        Get liabilities for a user, optionally filtered by type.

        Args:
            user: User object
            liability_type: Optional liability type to filter by

        Returns:
            QuerySet: Liability objects
        """
        from liabilities.models import Liability

        queryset = Liability.objects.filter(user=user, is_active=True)

        if liability_type:
            queryset = queryset.filter(liability_type=liability_type)

        return queryset

    @staticmethod
    def get_liability_breakdown(user):
        """
        Get breakdown of liabilities by type in user's home currency.

        Args:
            user: User object

        Returns:
            dict: Dictionary with liability types as keys and total balances as values
        """
        from liabilities.models import Liability

        home_currency = user.get_home_currency()
        breakdown = {}

        liabilities = Liability.objects.filter(user=user, is_active=True)

        for liability in liabilities:
            liability_type = liability.liability_type
            converted_balance = liability.get_balance_in_currency(home_currency)

            if liability_type in breakdown:
                breakdown[liability_type] += converted_balance
            else:
                breakdown[liability_type] = converted_balance

        return breakdown

    @staticmethod
    def calculate_total_monthly_payments(user):
        """
        Calculate total monthly payment obligations for a user.

        Args:
            user: User object

        Returns:
            Decimal: Total monthly payments in user's home currency
        """
        from liabilities.models import Liability

        home_currency = user.get_home_currency()
        total = Decimal('0.00')

        liabilities = Liability.objects.filter(
            user=user,
            is_active=True,
            monthly_payment__isnull=False
        )

        for liability in liabilities:
            if liability.monthly_payment:
                # Convert monthly payment to home currency
                converted_payment = liability.get_balance_in_currency(home_currency)
                # Scale based on the ratio of monthly payment to balance
                if liability.balance > 0:
                    payment_ratio = liability.monthly_payment / liability.balance
                    converted_payment = converted_payment * payment_ratio
                    total += converted_payment

        return total
