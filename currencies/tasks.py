"""
Celery tasks for currency and exchange rate management.
"""
from celery import shared_task
from .services import CurrencyService
import logging

logger = logging.getLogger(__name__)


@shared_task
def update_exchange_rates():
    """
    Celery task to update exchange rates from API.

    This task is scheduled to run daily at 9:00 AM UTC.
    Fetches latest exchange rates for USD (can be extended to other base currencies).

    Returns:
        dict: Results of the update operation
    """
    logger.info("Starting daily exchange rate update task")

    try:
        # Update rates for USD as base currency
        # You can add more base currencies here if needed: ['USD', 'EUR', 'GBP']
        results = CurrencyService.update_all_exchange_rates(base_currencies=['USD'])

        total_updated = sum(r['rates_updated'] for r in results.values())
        logger.info(f"Exchange rate update completed. Total rates updated: {total_updated}")

        return {
            'status': 'success',
            'results': results,
            'total_updated': total_updated
        }

    except Exception as e:
        logger.error(f"Error in exchange rate update task: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task
def update_exchange_rates_for_currencies(currency_codes):
    """
    Update exchange rates for specific base currencies.

    Args:
        currency_codes: List of currency codes to update

    Returns:
        dict: Results of the update operation
    """
    logger.info(f"Updating exchange rates for currencies: {currency_codes}")

    try:
        results = CurrencyService.update_all_exchange_rates(base_currencies=currency_codes)

        total_updated = sum(r['rates_updated'] for r in results.values())
        logger.info(f"Exchange rate update completed for {len(currency_codes)} currencies. Total rates updated: {total_updated}")

        return {
            'status': 'success',
            'results': results,
            'total_updated': total_updated
        }

    except Exception as e:
        logger.error(f"Error in exchange rate update task: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }
