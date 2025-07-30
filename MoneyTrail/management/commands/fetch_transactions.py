# MoneyTrail/management/commands/fetch_transactions.py
import requests
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from MoneyTrail.models import Transaction # Import your Transaction model
import dateutil.parser # pip install python-dateutil for robust date parsing

class Command(BaseCommand):
    help = 'Fetches dummy transaction data from an external API and saves it to the database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to fetch dummy transactions...'))

        api_url = "https://685efce5c55df675589d49df.mockapi.io/api/v1/transactions"

        try:
            response = requests.get(api_url)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            transactions_data = response.json()
        except requests.exceptions.RequestException as e:
            raise CommandError(f'Error fetching data from API: {e}')
        except ValueError as e: # For JSON decoding errors
            raise CommandError(f'Error decoding JSON response from API: {e}')

        if not transactions_data:
            self.stdout.write(self.style.WARNING('No transactions found in the API response.'))
            return

        # Reverse the order of transactions data.
        # This makes the oldest API transactions (e.g., API ID 24) get lower Django IDs (TRN-0001),
        # and newest API transactions (e.g., API ID 1) get higher Django IDs (TRN-0024).
        # This aligns the TRN-XXXX sequence with the chronological display when sorted by created_at.
        transactions_data.reverse()

        added_count = 0
        skipped_count = 0

        for data in transactions_data:
            external_id = data.get('id') # This is the ID from the external API
            amount_str = data.get('amount')
            transaction_type = data.get('type')
            created_at_str = data.get('createdAt')

            # Generate a default description for API transactions
            description = f"{transaction_type.capitalize()} from API"

            # Basic validation of API data
            if not all([external_id, amount_str, transaction_type, created_at_str]):
                self.stdout.write(self.style.WARNING(f'Skipping transaction due to missing data: {data}'))
                skipped_count += 1
                continue

            try:
                amount = Decimal(str(amount_str)) # Ensure amount is Decimal
                if amount <= 0:
                    self.stdout.write(self.style.WARNING(f'Skipping transaction {external_id} due to non-positive amount: {amount_str}'))
                    skipped_count += 1
                    continue
            except InvalidOperation:
                self.stdout.write(self.style.WARNING(f'Skipping transaction {external_id} due to invalid amount format: {amount_str}'))
                skipped_count += 1
                continue

            # Ensure type is valid
            if transaction_type not in [choice[0] for choice in Transaction.TRANSACTION_TYPES]:
                self.stdout.write(self.style.WARNING(f'Skipping transaction {external_id} due to invalid type: {transaction_type}'))
                skipped_count += 1
                continue

            try:
                # Use dateutil.parser for robust date parsing
                created_at = dateutil.parser.parse(created_at_str)
                # Ensure timezone-aware datetime
                if timezone.is_naive(created_at):
                    created_at = timezone.make_aware(created_at)
            except ValueError:
                self.stdout.write(self.style.WARNING(f'Skipping transaction {external_id} due to invalid date format: {created_at_str}'))
                skipped_count += 1
                continue

            try:
                # Check for duplicate api_external_id to avoid IntegrityError
                if not Transaction.objects.filter(api_external_id=external_id).exists():
                    Transaction.objects.create(
                        api_external_id=external_id, # Store the external ID here
                        description=description, # Save the generated description
                        amount=amount,
                        type=transaction_type,
                        created_at=created_at
                    )
                    self.stdout.write(self.style.SUCCESS(f'Successfully added API transaction: API-{external_id} - {amount:.2f} on {created_at.strftime("%Y-%m-%d")}'))
                    added_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f'Skipping duplicate API transaction: API-{external_id}'))
                    skipped_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error saving API transaction {external_id}: {e}'))
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(f'Finished fetching and saving dummy transactions. Added: {added_count}, Skipped: {skipped_count}'))

