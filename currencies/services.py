"""
Currency and Exchange Rate services for fetching and converting currencies.
"""
import requests
from decimal import Decimal
from datetime import date, timedelta
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from .models import Currency, ExchangeRate
import logging

logger = logging.getLogger(__name__)


class CurrencyService:
    """
    Service for managing currencies and exchange rates.

    Handles fetching exchange rates from external API,
    caching, and currency conversion.
    """

    CACHE_TIMEOUT = 86400  # 24 hours in seconds
    CACHE_KEY_PREFIX = 'exchange_rate'
    RATE_LIMIT_KEY = 'api_rate_limit_exchangerate'
    RATE_LIMIT_MAX_CALLS = 100  # Max API calls per window
    RATE_LIMIT_WINDOW = 3600  # Rate limit window in seconds (1 hour)

    @staticmethod
    def _check_rate_limit():
        """
        Check if API rate limit has been exceeded.

        Returns:
            bool: True if API call is allowed, False if rate limited

        Raises:
            Exception: If rate limit is exceeded
        """
        cache_key = CurrencyService.RATE_LIMIT_KEY
        current_count = cache.get(cache_key, 0)

        if current_count >= CurrencyService.RATE_LIMIT_MAX_CALLS:
            logger.warning(f"API rate limit exceeded: {current_count}/{CurrencyService.RATE_LIMIT_MAX_CALLS} calls in window")
            raise Exception(
                f"API rate limit exceeded. Maximum {CurrencyService.RATE_LIMIT_MAX_CALLS} calls per hour."
            )

        # Increment counter
        if current_count == 0:
            # First call in window, set expiry
            cache.set(cache_key, 1, CurrencyService.RATE_LIMIT_WINDOW)
        else:
            # Increment existing counter (preserve TTL)
            cache.incr(cache_key)

        return True

    @staticmethod
    def fetch_exchange_rates(base_currency='USD'):
        """
        Fetch exchange rates from ExchangeRate-API for a base currency.

        Args:
            base_currency: Base currency code (default: USD)

        Returns:
            dict: Dictionary of exchange rates or None if failed

        Example response:
        {
            'result': 'success',
            'base_code': 'USD',
            'rates': {
                'USD': 1,
                'EUR': 0.85,
                'GBP': 0.73,
                'INR': 83.12,
                ...
            }
        }
        """
        # Check rate limit before making API call
        try:
            CurrencyService._check_rate_limit()
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            return None

        url = f"{settings.EXCHANGE_RATE_API_URL}/{base_currency}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('result') == 'success':
                logger.info(f"Successfully fetched exchange rates for {base_currency}")
                return data
            else:
                logger.error(f"API returned error: {data.get('error-type', 'Unknown error')}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch exchange rates: {str(e)}")
            return None

    @staticmethod
    def update_exchange_rates_for_currency(base_currency_code='USD'):
        """
        Fetch and store exchange rates for a specific base currency.

        Args:
            base_currency_code: Base currency code to fetch rates for

        Returns:
            tuple: (success: bool, message: str, rates_updated: int)
        """
        try:
            # Get or create base currency
            base_currency, _ = Currency.objects.get_or_create(
                code=base_currency_code,
                defaults={
                    'name': f'{base_currency_code} Currency',
                    'symbol': base_currency_code,
                    'is_active': True
                }
            )

            # Fetch rates from API
            data = CurrencyService.fetch_exchange_rates(base_currency_code)

            if not data or 'rates' not in data:
                return False, "Failed to fetch exchange rates from API", 0

            rates = data['rates']
            today = date.today()
            rates_updated = 0

            # Store each exchange rate in a transaction (all-or-nothing)
            with transaction.atomic():
                for target_code, rate_value in rates.items():
                    # Get or create target currency
                    target_currency, _ = Currency.objects.get_or_create(
                        code=target_code,
                        defaults={
                            'name': f'{target_code} Currency',
                            'symbol': target_code,
                            'is_active': True
                        }
                    )

                    # Create or update exchange rate
                    ExchangeRate.objects.update_or_create(
                        from_currency=base_currency,
                        to_currency=target_currency,
                        date=today,
                        defaults={
                            'rate': Decimal(str(rate_value)),
                            'source': 'exchangerate-api'
                        }
                    )

                    # Cache the rate
                    cache_key = f"{CurrencyService.CACHE_KEY_PREFIX}_{base_currency_code}_{target_code}_{today}"
                    cache.set(cache_key, rate_value, CurrencyService.CACHE_TIMEOUT)

                    rates_updated += 1

            logger.info(f"Updated {rates_updated} exchange rates for {base_currency_code}")
            return True, f"Successfully updated {rates_updated} exchange rates", rates_updated

        except Exception as e:
            logger.error(f"Error updating exchange rates: {str(e)}")
            return False, f"Error: {str(e)}", 0

    @staticmethod
    def update_all_exchange_rates(base_currencies=None):
        """
        Update exchange rates for multiple base currencies.

        Args:
            base_currencies: List of currency codes to update. If None, uses USD only.

        Returns:
            dict: Summary of updates {currency: (success, message, count)}
        """
        if base_currencies is None:
            base_currencies = ['USD']

        results = {}

        for currency_code in base_currencies:
            success, message, count = CurrencyService.update_exchange_rates_for_currency(currency_code)
            results[currency_code] = {
                'success': success,
                'message': message,
                'rates_updated': count
            }

        return results

    @staticmethod
    def get_exchange_rate(from_currency, to_currency, date_obj=None):
        """
        Get exchange rate between two currencies.

        Args:
            from_currency: Source Currency object or code
            to_currency: Target Currency object or code
            date_obj: Date object (default: today)

        Returns:
            Decimal: Exchange rate or None if not found
        """
        # Convert to Currency objects if strings provided
        if isinstance(from_currency, str):
            try:
                from_currency = Currency.objects.get(code=from_currency)
            except Currency.DoesNotExist:
                logger.warning(f"Currency {from_currency} not found")
                return None

        if isinstance(to_currency, str):
            try:
                to_currency = Currency.objects.get(code=to_currency)
            except Currency.DoesNotExist:
                logger.warning(f"Currency {to_currency} not found")
                return None

        # Same currency
        if from_currency == to_currency:
            return Decimal('1.0')

        # Use today if no date specified
        if date_obj is None:
            date_obj = date.today()

        # Try cache first
        cache_key = f"{CurrencyService.CACHE_KEY_PREFIX}_{from_currency.code}_{to_currency.code}_{date_obj}"
        cached_rate = cache.get(cache_key)
        if cached_rate:
            return Decimal(str(cached_rate))

        # Try direct rate from database
        rate = ExchangeRate.get_rate_for_date(from_currency, to_currency, date_obj)

        if rate:
            # Cache it
            cache.set(cache_key, float(rate.rate), CurrencyService.CACHE_TIMEOUT)
            return rate.rate

        # Try inverse rate
        inverse_rate = ExchangeRate.get_rate_for_date(to_currency, from_currency, date_obj)
        if inverse_rate and inverse_rate.rate > 0:
            calculated_rate = Decimal('1.0') / inverse_rate.rate
            cache.set(cache_key, float(calculated_rate), CurrencyService.CACHE_TIMEOUT)
            return calculated_rate

        # Try to find rate for a recent date (within last 7 days)
        for days_back in range(1, 8):
            past_date = date_obj - timedelta(days=days_back)
            rate = ExchangeRate.get_rate_for_date(from_currency, to_currency, past_date)
            if rate:
                logger.info(f"Using rate from {past_date} for {from_currency.code}/{to_currency.code}")
                cache.set(cache_key, float(rate.rate), CurrencyService.CACHE_TIMEOUT)
                return rate.rate

        logger.warning(f"No exchange rate found for {from_currency.code} to {to_currency.code} on {date_obj}")
        return None

    @staticmethod
    def convert(amount, from_currency, to_currency, date_obj=None):
        """
        Convert an amount from one currency to another.

        Args:
            amount: Amount to convert (Decimal or float)
            from_currency: Source Currency object or code
            to_currency: Target Currency object or code
            date_obj: Date object (default: today)

        Returns:
            Decimal: Converted amount or original amount if conversion fails
        """
        if isinstance(amount, (int, float)):
            amount = Decimal(str(amount))

        rate = CurrencyService.get_exchange_rate(from_currency, to_currency, date_obj)

        if rate is None:
            logger.warning(f"Could not convert {amount} from {from_currency} to {to_currency}, returning original amount")
            return amount

        return amount * rate

    @staticmethod
    def get_all_active_currencies():
        """
        Get all active currencies.

        Returns:
            QuerySet: Active Currency objects
        """
        return Currency.objects.filter(is_active=True).order_by('code')

    @staticmethod
    def ensure_currency_exists(currency_code, name=None, symbol=None):
        """
        Ensure a currency exists in the database.

        Args:
            currency_code: Currency code (e.g., USD, EUR)
            name: Currency name (optional)
            symbol: Currency symbol (optional)

        Returns:
            Currency: Currency object
        """
        currency, created = Currency.objects.get_or_create(
            code=currency_code.upper(),
            defaults={
                'name': name or f'{currency_code} Currency',
                'symbol': symbol or currency_code,
                'is_active': True
            }
        )

        if created:
            logger.info(f"Created new currency: {currency_code}")

        return currency

    @staticmethod
    def bulk_get_exchange_rates(currency_pairs, date_obj=None):
        """
        Bulk fetch exchange rates for multiple currency pairs.

        Optimized to fetch all rates in a single query instead of N queries.

        Args:
            currency_pairs: List of tuples [(from_currency, to_currency), ...]
            date_obj: Date object (default: today)

        Returns:
            dict: {(from_code, to_code): rate, ...}
        """
        if date_obj is None:
            date_obj = date.today()

        rates_dict = {}

        # Extract unique currency codes
        from_codes = set()
        to_codes = set()
        for from_curr, to_curr in currency_pairs:
            from_code = from_curr.code if hasattr(from_curr, 'code') else from_curr
            to_code = to_curr.code if hasattr(to_curr, 'code') else to_curr
            from_codes.add(from_code)
            to_codes.add(to_code)

        # Bulk fetch all needed currencies
        all_codes = from_codes | to_codes
        currencies = Currency.objects.filter(code__in=all_codes).in_bulk(field_name='code')

        # Build list of currency ID pairs
        from_to_ids = []
        pair_to_codes = {}  # Map (from_id, to_id) -> (from_code, to_code)

        for from_curr, to_curr in currency_pairs:
            from_code = from_curr.code if hasattr(from_curr, 'code') else from_curr
            to_code = to_curr.code if hasattr(to_curr, 'code') else to_curr

            if from_code not in currencies or to_code not in currencies:
                continue

            from_id = currencies[from_code].id
            to_id = currencies[to_code].id

            # Same currency
            if from_code == to_code:
                rates_dict[(from_code, to_code)] = Decimal('1.0')
                continue

            from_to_ids.append((from_id, to_id))
            pair_to_codes[(from_id, to_id)] = (from_code, to_code)

        # Bulk fetch all exchange rates for the date
        if from_to_ids:
            # Build Q objects for all pairs
            from django.db.models import Q
            q_objects = Q()
            for from_id, to_id in from_to_ids:
                q_objects |= Q(from_currency_id=from_id, to_currency_id=to_id, date=date_obj)

            rates = ExchangeRate.objects.filter(q_objects).select_related('from_currency', 'to_currency')

            # Map results
            for rate_obj in rates:
                from_code = rate_obj.from_currency.code
                to_code = rate_obj.to_currency.code
                rates_dict[(from_code, to_code)] = rate_obj.rate

                # Cache it
                cache_key = f"{CurrencyService.CACHE_KEY_PREFIX}_{from_code}_{to_code}_{date_obj}"
                cache.set(cache_key, float(rate_obj.rate), CurrencyService.CACHE_TIMEOUT)

        return rates_dict

    @staticmethod
    def warm_cache_for_currencies(base_currency_codes=None):
        """
        Pre-warm cache with latest exchange rates for common currency pairs.

        Args:
            base_currency_codes: List of base currency codes to warm (default: ['USD'])

        Returns:
            int: Number of rates cached
        """
        if base_currency_codes is None:
            base_currency_codes = ['USD']

        today = date.today()
        cached_count = 0

        for base_code in base_currency_codes:
            try:
                base_currency = Currency.objects.get(code=base_code)

                # Fetch all latest rates for this base currency
                rates = ExchangeRate.objects.filter(
                    from_currency=base_currency,
                    date=today
                ).select_related('to_currency')

                for rate_obj in rates:
                    cache_key = f"{CurrencyService.CACHE_KEY_PREFIX}_{base_code}_{rate_obj.to_currency.code}_{today}"
                    cache.set(cache_key, float(rate_obj.rate), CurrencyService.CACHE_TIMEOUT)
                    cached_count += 1

            except Currency.DoesNotExist:
                logger.warning(f"Currency {base_code} not found for cache warming")
                continue

        logger.info(f"Warmed cache with {cached_count} exchange rates")
        return cached_count
