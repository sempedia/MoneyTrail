# MoneyTrail/serializers.py
from rest_framework import serializers
from .models import Transaction
import uuid # For generating unique transaction codes (though we'll use Django's ID now)

class TransactionSerializer(serializers.ModelSerializer):
    # Add a field for running_balance, which will be calculated in the view
    running_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    # Custom field to display the formatted transaction code (e.g., TRN-0001)
    display_code = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        # Include all fields for display and creation
        fields = ['id', 'display_code', 'api_external_id', 'description', 'amount', 'type', 'created_at', 'running_balance']
        # 'id' is Django's internal primary key
        # 'display_code' is generated from 'id'
        # 'api_external_id' is from the external API, not user-editable
        read_only_fields = ['id', 'display_code', 'api_external_id']

    def get_display_code(self, obj):
        """
        Returns a formatted transaction code based on Django's internal ID.
        e.g., TRN-0001, TRN-0010, TRN-0123
        """
        if obj.id:
            return f"TRN-{obj.id:04d}" # Formats ID with leading zeros to 4 digits
        return "TRN-N/A" # Should not happen for saved objects

    def validate_amount(self, value):
        """
        Check that the amount is positive.
        """
        if value <= 0:
            raise serializers.ValidationError("Amount must be a positive number.")
        return value

    def create(self, validated_data):
        """
        Custom create method to handle generation of api_external_id for new transactions
        if it's not provided (e.g., for manually added transactions).
        For API imports, api_external_id will be provided directly.
        """
        # Remove transaction_code from validated_data if it somehow made its way here,
        # as it's no longer a model field.
        validated_data.pop('transaction_code', None)

        # For manually added transactions, api_external_id will be null.
        # It's not generated for them, it's only for external API imports.
        return super().create(validated_data)

