# MoneyTrail/tests/test_models.py
from django.test import TestCase
from django.db.utils import IntegrityError
from MoneyTrail.models import Transaction
from decimal import Decimal
from django.utils import timezone
import uuid

class TransactionModelTest(TestCase):
    def setUp(self):
        # Create a sample transaction for testing
        self.transaction1 = Transaction.objects.create(
            api_external_id='API-123', # Using new field
            description='Initial Deposit',
            amount=Decimal('100.00'),
            type='deposit',
            created_at=timezone.datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        )
        self.transaction2 = Transaction.objects.create(
            api_external_id='API-456', # Using new field
            description='Coffee Purchase',
            amount=Decimal('50.00'),
            type='expense',
            created_at=timezone.datetime(2025, 1, 2, 11, 0, 0, tzinfo=timezone.utc)
        )
        # Manually added transaction (no api_external_id)
        self.transaction_manual = Transaction.objects.create(
            description='Manual Salary',
            amount=Decimal('200.00'),
            type='deposit',
            created_at=timezone.datetime(2025, 1, 3, 12, 0, 0, tzinfo=timezone.utc)
        )


    # Test that a transaction can be created successfully
    def test_transaction_creation(self):
        self.assertEqual(Transaction.objects.count(), 3)
        trans = Transaction.objects.get(api_external_id='API-123')
        self.assertEqual(trans.amount, Decimal('100.00'))
        self.assertEqual(trans.type, 'deposit')
        self.assertEqual(trans.description, 'Initial Deposit')

    # Test uniqueness of api_external_id
    def test_api_external_id_uniqueness(self):
        with self.assertRaises(IntegrityError):
            Transaction.objects.create(
                api_external_id='API-123', # Duplicate code
                description='Another Deposit',
                amount=Decimal('200.00'),
                type='deposit',
                created_at=timezone.now()
            )

    # Test string representation of the model (which now uses obj.id)
    def test_transaction_str_representation(self):
        # The ID will be auto-generated, so we fetch it to build the expected string
        trans1_from_db = Transaction.objects.get(pk=self.transaction1.pk)
        expected_str = f"TRN-{trans1_from_db.id:04d} - Deposit: 100.00 on 2025-01-01"
        self.assertEqual(str(trans1_from_db), expected_str)

        trans_manual_from_db = Transaction.objects.get(pk=self.transaction_manual.pk)
        expected_manual_str = f"TRN-{trans_manual_from_db.id:04d} - Deposit: 200.00 on 2025-01-03"
        self.assertEqual(str(trans_manual_from_db), expected_manual_str)


    # Test that amount is stored as Decimal
    def test_amount_decimal_type(self):
        trans = Transaction.objects.get(api_external_id='API-123')
        self.assertIsInstance(trans.amount, Decimal)

    # Test ordering (newest to oldest by default)
    def test_default_ordering(self):
        # When ordered by -created_at, transaction_manual (Jan 3) should be first,
        # then transaction2 (Jan 2), then transaction1 (Jan 1)
        transactions = Transaction.objects.all()
        self.assertEqual(transactions[0].description, 'Manual Salary')
        self.assertEqual(transactions[1].description, 'Coffee Purchase')
        self.assertEqual(transactions[2].description, 'Initial Deposit')

    # Test api_external_id field properties
    def test_api_external_id_field(self):
        field = Transaction._meta.get_field('api_external_id')
        self.assertTrue(field.unique)
        self.assertTrue(field.db_index)
        self.assertTrue(field.null)
        self.assertTrue(field.blank)
        self.assertEqual(field.max_length, 255)

    # Test description field properties
    def test_description_field(self):
        field = Transaction._meta.get_field('description')
        self.assertTrue(field.null)
        self.assertTrue(field.blank)
        self.assertEqual(field.max_length, 255)

    # Test transaction type choices
    def test_transaction_type_choices(self):
        field = Transaction._meta.get_field('type')
        self.assertEqual(field.choices, (('deposit', 'Deposit'), ('expense', 'Expense')))

    # Test default value for created_at
    def test_created_at_default(self):
        new_trans = Transaction.objects.create(
            description='Auto-generated test',
            amount=Decimal('10.00'),
            type='expense'
        )
        # Check if created_at is close to now (within a few seconds)
        self.assertAlmostEqual(new_trans.created_at, timezone.now(), delta=timezone.timedelta(seconds=5))
