import io
import re
import requests
from unittest.mock import patch
from django.core.management import call_command
from django.test import TestCase
from MoneyTrail.models import Transaction
from django.core.management.base import CommandError

# Helper function to strip ANSI escape codes
def strip_ansi_codes(s):
    return re.sub(r'\x1b\[[0-9;]*m', '', s)

class FetchTransactionsCommandTest(TestCase):
    @patch('requests.get')
    def test_command_creates_transactions(self, mock_get):
        # Mock the external API response
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = [
            {"createdAt": "2025-06-27T12:52:58.669Z", "amount": 41.42, "type": "expense", "id": "1"},
            {"createdAt": "2025-06-26T09:15:32.123Z", "amount": 75.80, "type": "deposit", "id": "2"},
            {"createdAt": "2025-06-25T10:00:00.000Z", "amount": 100.00, "type": "deposit", "id": "3"},
        ]

        out = io.StringIO()
        call_command('fetch_transactions', stdout=out)

        self.assertEqual(Transaction.objects.count(), 3)
        captured_output = strip_ansi_codes(out.getvalue())

        # Assert the exact messages from the command's output
        # Note: The output format in fetch_transactions.py uses "API-{id}" for messages
        self.assertIn('Successfully added API transaction: API-1 - 41.42 on 2025-06-27', captured_output)
        self.assertIn('Successfully added API transaction: API-2 - 75.80 on 2025-06-26', captured_output)
        self.assertIn('Successfully added API transaction: API-3 - 100.00 on 2025-06-25', captured_output)
        self.assertIn('Finished fetching and saving dummy transactions. Added: 3, Skipped: 0', captured_output)

        # Verify the actual stored transactions in the database
        t1 = Transaction.objects.get(api_external_id='1')
        t2 = Transaction.objects.get(api_external_id='2')
        t3 = Transaction.objects.get(api_external_id='3')

        # Check that their __str__ representation (which uses TRN-ID) is correct
        self.assertEqual(str(t1), f'TRN-{t1.id:04d} - Expense: 41.42 on 2025-06-27')
        self.assertEqual(str(t2), f'TRN-{t2.id:04d} - Deposit: 75.80 on 2025-06-26')
        self.assertEqual(str(t3), f'TRN-{t3.id:04d} - Deposit: 100.00 on 2025-06-25')


    @patch('requests.get')
    def test_command_skips_duplicates_on_multiple_runs(self, mock_get):
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = [
            {"createdAt": "2025-06-27T12:52:58.669Z", "amount": 41.42, "type": "expense", "id": "1"},
            {"createdAt": "2025-06-26T09:15:32.123Z", "amount": 75.80, "type": "deposit", "id": "2"},
            {"createdAt": "2025-06-25T10:00:00.000Z", "amount": 100.00, "type": "deposit", "id": "3"},
        ]

        # First run
        out1 = io.StringIO()
        call_command('fetch_transactions', stdout=out1)
        self.assertEqual(Transaction.objects.count(), 3)
        self.assertIn('Successfully added API transaction: API-1 - 41.42 on 2025-06-27', strip_ansi_codes(out1.getvalue()))

        # Second run with the same data
        out2 = io.StringIO()
        call_command('fetch_transactions', stdout=out2)
        self.assertEqual(Transaction.objects.count(), 3)
        captured_output2 = strip_ansi_codes(out2.getvalue())
        self.assertIn('Skipping duplicate API transaction: API-1', captured_output2)
        self.assertIn('Skipping duplicate API transaction: API-2', captured_output2)
        self.assertIn('Skipping duplicate API transaction: API-3', captured_output2)
        self.assertIn('Finished fetching and saving dummy transactions. Added: 0, Skipped: 3', captured_output2)

    @patch('requests.get')
    def test_command_handles_api_failure(self, mock_get):
        mock_get.return_value.ok = False
        mock_get.return_value.status_code = 500
        mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error", response=mock_get.return_value)

        out = io.StringIO()
        with self.assertRaisesMessage(CommandError, 'Error fetching data from API: 500 Server Error'):
            call_command('fetch_transactions', stdout=out)

        self.assertEqual(Transaction.objects.count(), 0)

