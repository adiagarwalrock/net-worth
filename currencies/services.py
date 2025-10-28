"""
Currency and Exchange Rate services for fetching and converting currencies.
"""
import requests
from decimal import Decimal
from datetime import date, timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
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

            # Store each exchange rate
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
                exchange_rate, created = ExchangeRate.objects.update_or_create(
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
