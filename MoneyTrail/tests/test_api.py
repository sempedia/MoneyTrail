import pytz
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from MoneyTrail.models import Transaction
# Assuming TEST_DAILY_EXPENSE_LIMIT is defined in views.py and is 2 for tests
from MoneyTrail.views import TEST_DAILY_EXPENSE_LIMIT, TransactionViewSet
from django.db.models import Sum, Case, When, F , DecimalField
class TransactionAPITest(APITestCase):
    def setUp(self):
        # Create transactions for testing.
        # Django's 'id' will be auto-generated.
        # api_external_id is used for transactions coming from the external API.
        self.transaction1 = Transaction.objects.create(
            description='Initial Deposit',
            amount=Decimal('1000.00'),
            type='deposit',
            api_external_id='1', # External ID for API-sourced transaction
            created_at=timezone.datetime(2025, 1, 1, 10, 0, 0, tzinfo=pytz.utc)
        )
        self.transaction2 = Transaction.objects.create(
            description='Groceries',
            amount=Decimal('50.00'),
            type='expense',
            api_external_id='2',
            created_at=timezone.datetime(2025, 1, 2, 12, 0, 0, tzinfo=pytz.utc)
        )
        self.transaction3 = Transaction.objects.create(
            description='Freelance Payment',
            amount=Decimal('200.00'),
            type='deposit',
            api_external_id='3',
            created_at=timezone.datetime(2025, 1, 3, 9, 0, 0, tzinfo=pytz.utc)
        )

        # Calculate the expected initial total balance
        self.initial_total_balance = Decimal('1150.00') # 1000 - 50 + 200

    def test_list_transactions_with_running_balance_and_pagination(self):
        response = self.client.get('/api/transactions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertIn('total_balance', data)
        self.assertIn('transactions', data)
        self.assertIn('has_more', data)
        self.assertIn('balance_history', data)

        self.assertEqual(len(data['transactions']), 3)
        self.assertEqual(Decimal(str(data['total_balance'])), self.initial_total_balance)

        # Verify display codes and running balances (ordered newest to oldest as per API response)
        # The model's default ordering is -created_at, so the list comes newest first.

        # Get actual transactions from DB to match their auto-generated IDs
        # and ensure correct order for comparison with API response.
        transactions_from_db_ordered_desc = Transaction.objects.all().order_by('-created_at')

        # Transaction 3 (newest)
        self.assertEqual(data['transactions'][0]['id'], transactions_from_db_ordered_desc[0].id)
        self.assertEqual(data['transactions'][0]['display_code'], f'TRN-{transactions_from_db_ordered_desc[0].id:04d}')
        self.assertEqual(Decimal(str(data['transactions'][0]['running_balance'])), Decimal('1150.00'))

        # Transaction 2
        self.assertEqual(data['transactions'][1]['id'], transactions_from_db_ordered_desc[1].id)
        self.assertEqual(data['transactions'][1]['display_code'], f'TRN-{transactions_from_db_ordered_desc[1].id:04d}')
        self.assertEqual(Decimal(str(data['transactions'][1]['running_balance'])), Decimal('950.00'))

        # Transaction 1 (oldest)
        self.assertEqual(data['transactions'][2]['id'], transactions_from_db_ordered_desc[2].id)
        self.assertEqual(data['transactions'][2]['display_code'], f'TRN-{transactions_from_db_ordered_desc[2].id:04d}')
        self.assertEqual(Decimal(str(data['transactions'][2]['running_balance'])), Decimal('1000.00'))

        # Verify balance history data (ordered chronologically, oldest to newest)
        self.assertEqual(len(data['balance_history']), 3)
        self.assertEqual(data['balance_history'][0]['date'], '2025-01-01')
        self.assertEqual(data['balance_history'][0]['balance'], 1000.0)
        self.assertEqual(data['balance_history'][1]['date'], '2025-01-02')
        self.assertEqual(data['balance_history'][1]['balance'], 950.0)
        self.assertEqual(data['balance_history'][2]['date'], '2025-01-03')
        self.assertEqual(data['balance_history'][2]['balance'], 1150.0)



    def test_create_deposit_transaction(self):

        data = {
            'description': 'New Deposit',
            'amount': '500.00',
            'type': 'deposit',
            'created_at': '2025-01-04'
        }
        response = self.client.post('/api/transactions/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 4)

        new_transaction_id = response.json()['new_transaction']['id']
        new_transaction = Transaction.objects.get(pk=new_transaction_id)

        self.assertEqual(new_transaction.description, 'New Deposit')
        self.assertEqual(new_transaction.amount, Decimal('500.00'))
        self.assertEqual(new_transaction.type, 'deposit')
        self.assertTrue(new_transaction.id is not None)

        expected_balance = self.initial_total_balance + Decimal('500.00')
        actual_balance = Decimal(str(response.json()['total_balance']))

        self.assertEqual(response.json()['new_transaction']['display_code'], f'TRN-{new_transaction.id:04d}')
        self.assertEqual(actual_balance, expected_balance)

    def test_create_expense_transaction(self):
        data = {
            'description': 'New Expense',
            'amount': '100.00',
            'type': 'expense',
            'created_at': '2025-01-04'
        }
        response = self.client.post('/api/transactions/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 4)

        new_transaction_id = response.json()['new_transaction']['id']
        new_transaction = Transaction.objects.get(pk=new_transaction_id)

        self.assertEqual(new_transaction.description, 'New Expense')
        self.assertEqual(new_transaction.amount, Decimal('100.00'))
        self.assertEqual(new_transaction.type, 'expense')
        self.assertTrue(new_transaction.id is not None)

        # Check display_code from the API response
        self.assertEqual(response.json()['new_transaction']['display_code'], f'TRN-{new_transaction.id:04d}')

        # Check updated total balance
        self.assertEqual(Decimal(str(response.json()['total_balance'])), self.initial_total_balance - Decimal('100.00'))

    def test_create_transaction_negative_amount_fails(self):
        data = {
            'description': 'Invalid Amount',
            'amount': '-50.00',
            'type': 'deposit',
            'created_at': '2025-01-04'
        }
        response = self.client.post('/api/transactions/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.json())
        self.assertIn('Amount must be a positive number.', response.json()['amount'][0])
        self.assertEqual(Transaction.objects.count(), 3)

    def test_create_transaction_zero_amount_fails(self):
        data = {
            'description': 'Invalid Amount',
            'amount': '0.00',
            'type': 'deposit',
            'created_at': '2025-01-04'
        }
        response = self.client.post('/api/transactions/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.json())
        self.assertIn('Amount must be a positive number.', response.json()['amount'][0])
        self.assertEqual(Transaction.objects.count(), 3)

    def test_create_expense_overspending_fails(self):
        # Current balance is self.initial_total_balance (1150.00)
        data = {
            'description': 'Too Much Expense',
            'amount': '1200.00', # More than current balance
            'type': 'expense',
            'created_at': '2025-01-04'
        }
        response = self.client.post('/api/transactions/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.json())
        self.assertEqual(response.json()['detail'], 'Not enough balance. Cannot add expense.')
        self.assertEqual(Transaction.objects.count(), 3)

    def test_daily_expense_limit(self):
        # Create a large deposit to ensure balance is not an issue
        Transaction.objects.create(
            description='Large Deposit for Daily Limit Test',
            amount=Decimal('5000.00'),
            type='deposit',
            created_at=timezone.datetime(2025, 1, 5, 9, 0, 0, tzinfo=pytz.utc)
        )

        # Add exactly TEST_DAILY_EXPENSE_LIMIT expenses for the same day (e.g., 2 if limit is 2)
        for i in range(TEST_DAILY_EXPENSE_LIMIT):
            Transaction.objects.create(
                description=f'Daily Expense {i+1}',
                amount=Decimal('10.00'),
                type='expense',
                created_at=timezone.datetime(2025, 1, 5, 10, i, 0, tzinfo=pytz.utc)
            )

        # Attempt to add the expense that exceeds the daily limit (TEST_DAILY_EXPENSE_LIMIT + 1)
        data = {
            'description': 'Over Limit Expense',
            'amount': '10.00',
            'type': 'expense',
            'created_at': '2025-01-05T11:00:00Z'
        }
        response = self.client.post('/api/transactions/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.json())
        self.assertEqual(response.json()['detail'], f'Daily expense limit reached ({TEST_DAILY_EXPENSE_LIMIT} expenses per day).')

        # Ensure no new expense was created (count remains at the limit)
        count = Transaction.objects.filter(
            type='expense',
            created_at__date=timezone.datetime(2025, 1, 5, tzinfo=pytz.utc).date()
        ).count()
        self.assertEqual(count, TEST_DAILY_EXPENSE_LIMIT)

    def test_retrieve_transaction(self):
        response = self.client.get(f'/api/transactions/{self.transaction1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assert against the dynamic display_code (TRN-ID) from the serializer
        self.assertEqual(response.json()['display_code'], f'TRN-{self.transaction1.id:04d}')
    def test_update_transaction(self):
        updated_data = {
            'description': 'Updated Deposit',
            'amount': '1500.00',
            'type': 'deposit',
            'created_at': '2025-01-01'
        }

        response = self.client.put(f'/api/transactions/{self.transaction1.id}/', updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.transaction1.refresh_from_db()
        self.assertEqual(self.transaction1.description, 'Updated Deposit')
        self.assertEqual(self.transaction1.amount, Decimal('1500.00'))

        # Use the viewset's _recalculate_balances to get expected total_balance
        viewset = TransactionViewSet()
        total_balance, _, _ = viewset._recalculate_balances()
        expected_total = total_balance

        print(f"DEBUG: expected_total={expected_total}, response_total={response.json()['total_balance']}")

        self.assertEqual(Decimal(str(response.json()['total_balance'])), expected_total)
    def test_partial_update_transaction(self):
        partial_data = {
            'amount': '75.00'
        }
        response = self.client.patch(f'/api/transactions/{self.transaction2.id}/', partial_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.transaction2.refresh_from_db()
        self.assertEqual(self.transaction2.amount, Decimal('75.00'))

        # Use the viewset's _recalculate_balances to get expected total_balance
        viewset = TransactionViewSet()
        expected_total, _, _ = viewset._recalculate_balances()

        print(f"DEBUG: expected_total={expected_total}, response_total={response.json()['total_balance']}")

        self.assertEqual(Decimal(str(response.json()['total_balance'])), expected_total)

    def test_delete_transaction(self):
        response = self.client.delete(f'/api/transactions/{self.transaction1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Transaction.objects.count(), 2)

        # Fetch transactions again to get the new total balance
        list_response = self.client.get('/api/transactions/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        list_data = list_response.json()

        # Original: 1000 (t1) - 50 (t2) + 200 (t3) = 1150
        # Deleted t1 (1000)
        # New total: -50 + 200 = 150
        self.assertEqual(Decimal(str(list_data['total_balance'])), Decimal('150.00'))

