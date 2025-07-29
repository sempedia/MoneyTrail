from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from MoneyTrail.models import Transaction

# Mock API response for consistent testing
MOCK_API_RESPONSE = [
    {
        "createdAt": "2025-06-27T12:52:58.669Z",
        "amount": 41.42,
        "type": "expense",
        "id": "1"
    },
    {
        "createdAt": "2025-06-26T09:15:32.123Z",
        "amount": 75.80,
        "type": "deposit",
        "id": "2"
    },
    {
        "createdAt": "2025-06-25T09:15:32.123Z",
        "amount": 100.00,
        "type": "deposit",
        "id": "3"
    },
]

# Mock the requests.get method to return our predefined response
# This prevents actual external API calls during tests
import requests
from unittest.mock import patch

class FetchTransactionsCommandTest(TestCase):
    # Test that the command runs successfully and creates transactions.
    @patch('requests.get') # Mock requests.get
    def test_command_creates_transactions(self, mock_get):
        # Configure the mock to return our sample response
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = MOCK_API_RESPONSE
        mock_get.return_value.raise_for_status.return_value = None # Mock successful status

        # Ensure no transactions exist initially
        self.assertEqual(Transaction.objects.count(), 0)

        # Call the management command
        out = StringIO()
        call_command('fetch_transactions', stdout=out)

        # Check that transactions were created (based on MOCK_API_RESPONSE)
        self.assertEqual(Transaction.objects.count(), len(MOCK_API_RESPONSE))

        # Check the command's output for success messages
        self.assertIn('Starting to fetch dummy transactions...', out.getvalue())
        self.assertIn('Successfully added transaction:', out.getvalue())
        self.assertIn('Finished fetching and saving dummy transactions.', out.getvalue())

    # Test that running the command multiple times skips duplicates.
    @patch('requests.get')
    def test_command_skips_duplicates_on_multiple_runs(self, mock_get):
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = MOCK_API_RESPONSE
        mock_get.return_value.raise_for_status.return_value = None

        # Run once - should add all transactions from MOCK_API_RESPONSE
        out1 = StringIO()
        call_command('fetch_transactions', stdout=out1)
        self.assertEqual(Transaction.objects.count(), len(MOCK_API_RESPONSE))
        self.assertIn('Successfully added transaction:', out1.getvalue())
        self.assertNotIn('Skipping duplicate transaction:', out1.getvalue())

        # Run again - should skip all transactions as they are duplicates
        out2 = StringIO()
        call_command('fetch_transactions', stdout=out2)
        # The count should remain the same as no new unique transactions are added
        self.assertEqual(Transaction.objects.count(), len(MOCK_API_RESPONSE))
        # Check that the output indicates skipping duplicates
        self.assertIn('Skipping duplicate transaction:', out2.getvalue())
        self.assertNotIn('Successfully added transaction:', out2.getvalue()) # No new successful adds
