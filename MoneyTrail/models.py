# MoneyTrail/models.py
from django.db import models
from django.utils import timezone
from decimal import Decimal
import uuid # For generating unique transaction codes (though we'll use Django's ID now)

class Transaction(models.Model):
    # Choices for transaction type
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('expense', 'Expense'),
    )

    # Django's default 'id' field (auto-incrementing integer) will be used
    # to generate the sequential display code (e.g., TRN-0001).

    # Stores the original 'id' from the external API, if applicable.
    # This is nullable because manually added transactions won't have an external ID.
    api_external_id = models.CharField(max_length=255, unique=True, db_index=True, null=True, blank=True)

    # A description for the transaction (e.g., "Groceries", "Salary").
    # This field is used in the UI form.
    description = models.CharField(max_length=255, blank=True, null=True)

    # Amount of the transaction. Stored as positive; type determines debit/credit.
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Type of transaction: 'deposit' or 'expense'
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)

    # Date and time when the transaction was created.
    # For API imports, this will be parsed from 'createdAt'.
    # For manual, it defaults to now.
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        # Order transactions by creation date, newest first.
        # This is crucial for running balance calculation and display.
        ordering = ['-created_at']

    def __str__(self):
        # Use Django's auto-generated 'id' for the display code
        display_code = f"TRN-{self.id:04d}" if self.id else "N/A"
        return f"{display_code} - {self.type.capitalize()}: {self.amount} on {self.created_at.strftime('%Y-%m-%d')}"
