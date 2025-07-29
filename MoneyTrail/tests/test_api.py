# MoneyTrail/tests/test_api.py
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from MoneyTrail.models import Transaction
from decimal import Decimal
from django.utils import timezone
import uuid # For generating transaction codes in tests

class TransactionAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_url = reverse('transaction-list') # /api/transactions/

        # Create some initial transactions for testing list, running balance, and pagination
        # Order matters for running balance calculation
        self.trans1_deposit = Transaction.objects.create(
            api_external_id='API-001',
            description='Initial Deposit',
            amount=Decimal('100.00'),
            type='deposit',
            created_at=timezone.datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        )
        self.trans2_expense = Transaction.objects.create(
            api_external_id='API-002',
            description='Coffee',
            amount=Decimal('30.00'),
            type='expense',
            created_at=timezone.datetime(2025, 1, 2, 11, 0, 0, tzinfo=timezone.utc)
        )
        self.trans3_deposit = Transaction.objects.create(
            api_external_id='API-003',
            description='Freelance Payment',
            amount=Decimal('50.00'),
            type='deposit',
            created_at=timezone.datetime(2025, 1, 3, 12, 0, 0, tzinfo=timezone.utc)
        )
        self.trans4_expense = Transaction.objects.create(
            api_external_id='API-004',
            description='Groceries',
            amount=Decimal('20.00'),
            type='expense',
            created_at=timezone.datetime(2025, 1, 4, 13, 0, 0, tzinfo=timezone.utc)
        )

        # Detail URL for a specific transaction (using pk as it's the internal ID)
        self.detail_url = reverse('transaction-detail', kwargs={'pk': self.trans1_deposit.pk})


    # Test creating a new deposit transaction via the API (POST request).
    def test_create_deposit_transaction(self):
        new_transaction_data = {
            "description": "New Deposit from Client",
            "amount": "500.00",
            "type": "deposit",
            "created_at": "2025-07-29T10:00:00Z" # Use ISO format for datetime
        }
        response = self.client.post(self.list_url, new_transaction_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 5) # 4 existing + 1 new
        # Check that display_code is auto-generated and formatted
        self.assertTrue(response.data['new_transaction']['display_code'].startswith('TRN-'))
        self.assertEqual(response.data['new_transaction']['description'], 'New Deposit from Client')
        self.assertEqual(Decimal(response.data['new_transaction']['amount']), Decimal('500.00'))
        self.assertEqual(response.data['new_transaction']['type'], 'deposit')
        # Check that total balance is updated
        self.assertAlmostEqual(Decimal(response.data['total_balance']), Decimal('600.00'), places=2) # 100-30+50-20 + 500 = 600

    # Test creating a new expense transaction via the API (POST request).
    def test_create_expense_transaction(self):
        new_transaction_data = {
            "description": "Lunch with friends",
            "amount": "10.00",
            "type": "expense",
            "created_at": "2025-07-29T10:00:00Z"
        }
        response = self.client.post(self.list_url, new_transaction_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 5)
        self.assertTrue(response.data['new_transaction']['display_code'].startswith('TRN-'))
        self.assertEqual(response.data['new_transaction']['description'], 'Lunch with friends')
        self.assertEqual(Decimal(response.data['new_transaction']['amount']), Decimal('10.00'))
        self.assertEqual(response.data['new_transaction']['type'], 'expense')
        self.assertAlmostEqual(Decimal(response.data['total_balance']), Decimal('90.00'), places=2) # 100-30+50-20 - 10 = 90

    # Test validation: Amount must be positive
    def test_create_transaction_negative_amount_fails(self):
        invalid_data = {
            "description": "Invalid test",
            "amount": "-10.00",
            "type": "deposit",
            "created_at": "2025-07-29T10:00:00Z"
        }
        response = self.client.post(self.list_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Amount must be a positive number.', response.data['amount'][0])
        self.assertEqual(Transaction.objects.count(), 4) # No new transaction created

    def test_create_transaction_zero_amount_fails(self):
        invalid_data = {
            "description": "Invalid test",
            "amount": "0.00",
            "type": "deposit",
            "created_at": "2025-07-29T10:00:00Z"
        }
        response = self.client.post(self.list_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Amount must be a positive number.', response.data['amount'][0])
        self.assertEqual(Transaction.objects.count(), 4)

    # Test validation: Overspending (expense results in negative balance)
    def test_create_expense_overspending_fails(self):
        # Current balance: 100 - 30 + 50 - 20 = 100
        # Try to add an expense larger than current balance
        invalid_data = {
            "description": "Too much expense",
            "amount": "101.00", # More than current balance of 100
            "type": "expense",
            "created_at": "2025-07-29T10:00:00Z"
        }
        response = self.client.post(self.list_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Not enough balance. Cannot add expense.')
        self.assertEqual(Transaction.objects.count(), 4)

    # Test validation: Daily expense limit (200 expenses per day)
    def test_daily_expense_limit(self):
        # Create 200 expenses for a specific day
        test_date = timezone.datetime(2025, 7, 28, 10, 0, 0, tzinfo=timezone.utc)
        for i in range(200):
            # Ensure unique api_external_id for these test transactions
            Transaction.objects.create(
                api_external_id=f'TEST-EXP-{i}-{uuid.uuid4().hex[:4]}',
                description=f'Daily Expense {i}',
                amount=Decimal('1.00'),
                type='expense',
                created_at=test_date + timezone.timedelta(seconds=i) # Slightly different times
            )
        self.assertEqual(Transaction.objects.filter(type='expense', created_at__date=test_date.date()).count(), 200)

        # Try to add one more expense for the same day
        new_expense_data = {
            "description": "Over limit expense",
            "amount": "5.00",
            "type": "expense",
            "created_at": test_date.isoformat() # Same date as the 200 expenses
        }
        response = self.client.post(self.list_url, new_expense_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Daily expense limit reached (200 expenses per day).')
        # Count should still be 200 for that day
        self.assertEqual(Transaction.objects.filter(type='expense', created_at__date=test_date.date()).count(), 200)


    # Test retrieving a list of transactions with running balance and pagination.
    def test_list_transactions_with_running_balance_and_pagination(self):
        # Test default page (page 1, 10 items)
        response = self.client.get(self.list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_balance', response.data)
        self.assertIn('transactions', response.data)
        self.assertIn('has_more', response.data)

        # Check total balance (100 - 30 + 50 - 20 = 100)
        self.assertAlmostEqual(Decimal(response.data['total_balance']), Decimal('100.00'), places=2)

        # Check pagination (should return all 4 transactions, as page size is 10)
        self.assertEqual(len(response.data['transactions']), 4)
        self.assertFalse(response.data['has_more'])

        # Check running balances (ordered newest to oldest from view)
        # Order: trans4 (1/4), trans3 (1/3), trans2 (1/2), trans1 (1/1)
        # Balances:
        # trans1: 100
        # trans2: 100 - 30 = 70
        # trans3: 70 + 50 = 120
        # trans4: 120 - 20 = 100 (final balance)
        # When reversed for display:
        # trans4: 100.00
        # trans3: 120.00
        # trans2: 70.00
        # trans1: 100.00

        transactions_in_response = response.data['transactions']
        # Check display_code format
        self.assertTrue(transactions_in_response[0]['display_code'].startswith('TRN-'))
        self.assertEqual(transactions_in_response[0]['description'], 'Groceries')
        self.assertAlmostEqual(Decimal(transactions_in_response[0]['running_balance']), Decimal('100.00'), places=2)


    # Test retrieving a single transaction (GET request to detail endpoint).
    def test_retrieve_transaction(self):
        response = self.client.get(self.detail_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['api_external_id'], self.trans1_deposit.api_external_id)
        self.assertEqual(response.data['description'], self.trans1_deposit.description)
        self.assertEqual(Decimal(response.data['amount']), self.trans1_deposit.amount)
        self.assertEqual(response.data['type'], self.trans1_deposit.type)
        self.assertTrue(response.data['display_code'].startswith('TRN-'))


    # Test updating an existing transaction (PUT request).
    def test_update_transaction(self):
        updated_data = {
            "description": "Updated Initial Deposit",
            "amount": "150.00",
            "type": "expense",
            "created_at": self.trans1_deposit.created_at.isoformat() # Must provide existing created_at
        }
        response = self.client.put(self.detail_url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.trans1_deposit.refresh_from_db()
        self.assertEqual(self.trans1_deposit.description, "Updated Initial Deposit")
        self.assertEqual(self.trans1_deposit.amount, Decimal('150.00'))
        self.assertEqual(self.trans1_deposit.type, "expense")

    # Test partially updating an existing transaction (PATCH request).
    def test_partial_update_transaction(self):
        partial_data = {
            "description": "Partial Update Test",
            "amount": "120.00"
        }
        response = self.client.patch(self.detail_url, partial_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.trans1_deposit.refresh_from_db()
        self.assertEqual(self.trans1_deposit.description, "Partial Update Test")
        self.assertEqual(self.trans1_deposit.amount, Decimal('120.00'))
        # Other fields should be unchanged
        self.assertEqual(self.trans1_deposit.type, "deposit")

    # Test deleting an existing transaction (DELETE request).
    def test_delete_transaction(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Transaction.objects.count(), 3) # 4 - 1 = 3
        with self.assertRaises(Transaction.DoesNotExist):
            Transaction.objects.get(pk=self.trans1_deposit.pk)

