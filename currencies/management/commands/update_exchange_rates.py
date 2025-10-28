"""
Management command to update exchange rates from API.

Usage:
    python manage.py update_exchange_rates
    python manage.py update_exchange_rates --currencies USD EUR GBP
"""
from django.core.management.base import BaseCommand
from currencies.services import CurrencyService


class Command(BaseCommand):
    help = 'Update exchange rates from ExchangeRate-API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--currencies',
            nargs='+',
            type=str,
            default=['USD'],
            help='Base currencies to fetch rates for (default: USD)'
        )

    def handle(self, *args, **options):
        """
        Execute the command.

        Inputs:
            currencies: List of currency codes to fetch rates for

        Outputs:
            Console output showing results of update operation
        """
        currencies = options['currencies']

        self.stdout.write(
            self.style.WARNING(f'Fetching exchange rates for: {", ".join(currencies)}')
        )

        results = CurrencyService.update_all_exchange_rates(base_currencies=currencies)

        self.stdout.write('\n' + '='*60)
        self.stdout.write('EXCHANGE RATE UPDATE RESULTS')
        self.stdout.write('='*60 + '\n')

        for currency_code, result in results.items():
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ {currency_code}: {result["message"]} ({result["rates_updated"]} rates)'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ {currency_code}: {result["message"]}'
                    )
                )

        total_updated = sum(r['rates_updated'] for r in results.values())
        self.stdout.write('\n' + '-'*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'Total rates updated: {total_updated}'
            )
        )
        self.stdout.write('-'*60 + '\n')
