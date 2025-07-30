# MoneyTrail/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from django.views.generic import TemplateView
from django.db.models import Sum, Q, When, F, DecimalField, Value, Case, ExpressionWrapper
from django.db import transaction as db_transaction # Avoid name conflict with model
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import pytz # pip install pytz for timezone handling
from django.conf import settings
from django.core.management import call_command # For fetch_external_transactions_api
from django.db.models.functions import Coalesce
from .models import Transaction
from .serializers import TransactionSerializer

# Get the timezone from Django settings or default to UTC
TIME_ZONE = pytz.timezone(getattr(settings, 'TIME_ZONE', 'UTC'))

# --- Define a temporary daily expense limit for testing ---
# Set to a small number like 5 or 10 for easy testing.
# REMEMBER TO CHANGE THIS BACK TO 200 FOR PRODUCTION!
TEST_DAILY_EXPENSE_LIMIT = 2
# --- End temporary limit ---


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    # No authentication/permissions needed as per requirements (AllowAny is default)

    def get_queryset(self):
        return Transaction.objects.all().order_by('-created_at')

    def _recalculate_balances(self, filtered_queryset=None):
        """
        Helper to recalculate all running balances and total balance based on a queryset.
        Also returns historical balance data for charting.
        """
        all_transactions = Transaction.objects.all().order_by('created_at')

        running_balance = Decimal('0.00')
        transactions_with_balance = []
        balance_history = [] # To store (date, balance) for charting

        # Add an initial point for the chart if there are no transactions
        # or if the first transaction is not at the very beginning of time.
        # This ensures the chart starts from 0 at an appropriate date.
        if not all_transactions.exists():
            balance_history.append({
                'date': timezone.now().date().isoformat(), # Today's date
                'balance': 0.0
            })

        # Calculate running balance for ALL transactions
        for trans in all_transactions:
            if trans.type == 'deposit':
                running_balance += trans.amount
            elif trans.type == 'expense':
                running_balance -= trans.amount
            trans.running_balance = running_balance
            transactions_with_balance.append(trans)
            # Store daily balance for charting (use end of day for consistency)
            # If multiple transactions on same day, chart will show final balance for that day.
            balance_history.append({
                'date': trans.created_at.date().isoformat(), # YYYY-MM-DD format
                'balance': float(running_balance) # Convert Decimal to float for JSON/Chart.js
            })

        # Now, filter this list of transactions_with_balance based on the provided filtered_queryset
        if filtered_queryset is not None:
            filtered_ids = set(filtered_queryset.values_list('id', flat=True))
            display_transactions = [t for t in transactions_with_balance if t.id in filtered_ids]
        else:
            display_transactions = transactions_with_balance

        # Reverse for newest to oldest display for the *display_transactions*
        display_transactions.reverse()

        total_balance = Decimal('0.00')
        if transactions_with_balance: # Check the full list for the true total balance
            total_balance = transactions_with_balance[-1].running_balance # Last item in chronological list

        return total_balance, display_transactions, balance_history

    def list(self, request, *args, **kwargs):
        queryset = Transaction.objects.all()

        filter_type = request.query_params.get('type')
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        description_search = request.query_params.get('description_search')
        code_search = request.query_params.get('code_search')

        if filter_type:
            queryset = queryset.filter(type=filter_type)

        if start_date_str:
            try:
                start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=start_date)
            except ValueError:
                return Response({'detail': 'Invalid start_date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        if end_date_str:
            try:
                end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=end_date)
            except ValueError:
                return Response({'detail': 'Invalid end_date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        if description_search:
            queryset = queryset.filter(description__icontains=description_search)

        if code_search:
            parsed_id = None
            if code_search.startswith('TRN-'):
                try:
                    parsed_id = int(code_search[4:])
                except ValueError:
                    pass
            else:
                try:
                    parsed_id = int(code_search)
                except ValueError:
                    pass

            if parsed_id is not None:
                queryset = queryset.filter(id=parsed_id)
            else:
                queryset = queryset.none()

        total_balance, transactions_with_balance_for_display, balance_history = self._recalculate_balances(filtered_queryset=queryset)

        page_size = 10
        page = int(request.query_params.get('page', 1))
        offset = (page - 1) * page_size
        limit = offset + page_size

        paginated_transactions = transactions_with_balance_for_display[offset:limit]

        serializer = self.get_serializer(paginated_transactions, many=True)

        return Response({
            'total_balance': total_balance,
            'transactions': serializer.data,
            'has_more': len(transactions_with_balance_for_display) > limit,
            'balance_history': balance_history # Include balance history for the chart
        })




    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data['amount']
        transaction_type = serializer.validated_data['type']
        created_at = serializer.validated_data.get('created_at', timezone.now())

        if timezone.is_naive(created_at):
            created_at = timezone.make_aware(created_at, timezone=TIME_ZONE)

        # --- VALIDATIONS ---
        if transaction_type == 'expense':
            transaction_date = created_at.date()

            # Daily expense limit check
            daily_expenses_count = Transaction.objects.filter(
                type='expense',
                created_at__date=transaction_date
            ).count()

            print(f"DEBUG: Checking daily expense limit for {transaction_date}. Current count: {daily_expenses_count}")

            if daily_expenses_count >= TEST_DAILY_EXPENSE_LIMIT:
                print(f"DEBUG: Daily expense limit of {TEST_DAILY_EXPENSE_LIMIT} reached for {transaction_date}.")
                return Response(
                    {'detail': f'Daily expense limit reached ({TEST_DAILY_EXPENSE_LIMIT} expenses per day).'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Sufficient balance check
            current_total_balance = Transaction.objects.aggregate(
                total=Coalesce(Sum(
                    Case(
                        When(type='deposit', then=F('amount')),
                        When(type='expense', then=ExpressionWrapper(F('amount') * Decimal('-1'), output_field=DecimalField())),
                        default=Value(0),
                        output_field=DecimalField()
                    )
                ), Value(0, output_field=DecimalField()))
            )['total'] or Decimal('0.00')

            print(f"DEBUG: Checking sufficient balance. Current total balance: {current_total_balance}, Attempted expense: {amount}")

            if current_total_balance < amount:
                print(f"DEBUG: Insufficient balance. Current: {current_total_balance}, Expense: {amount}")
                return Response(
                    {'detail': 'Not enough balance. Cannot add expense.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        # --- END VALIDATIONS ---

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        total_balance_after_create, transactions_with_balance_after_create, balance_history_after_create = self._recalculate_balances()

        return Response({
            'total_balance': transactions_with_balance_after_create[0].running_balance if transactions_with_balance_after_create else Decimal('0.00'),
            'new_transaction': serializer.data,
            'transactions': self.get_serializer(transactions_with_balance_after_create[:10], many=True).data,
            'balance_history': balance_history_after_create
        }, status=status.HTTP_201_CREATED, headers=headers)

    @db_transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data.get('amount', instance.amount)
        transaction_type = serializer.validated_data.get('type', instance.type)
        created_at = serializer.validated_data.get('created_at', instance.created_at)

        if timezone.is_naive(created_at):
            created_at = timezone.make_aware(created_at, timezone=TIME_ZONE)

        if amount <= 0:
            return Response(
                {'detail': 'Amount must be a positive number.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if transaction_type == 'expense':
            balance_excluding_current = Transaction.objects.exclude(pk=instance.pk).aggregate(
            total=Sum(
                Case(
                    When(type='deposit', then=F('amount')),
                    When(type='expense', then=-F('amount')),
                    output_field=DecimalField()
                )
            )
        )['total'] or Decimal('0.00')

            potential_new_balance = balance_excluding_current - amount

            print(f"DEBUG: Updating expense. Balance excluding current: {balance_excluding_current}, New expense amount: {amount}, Potential new balance: {potential_new_balance}")

            if potential_new_balance < 0:
                print(f"DEBUG: Update would result in negative balance. Current: {balance_excluding_current}, New Expense: {amount}")
                return Response(
                    {'detail': 'Updating this expense would result in a negative balance.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if transaction_type == 'expense' and (instance.type != 'expense' or instance.created_at.date() != created_at.date()):
            transaction_date = created_at.date()
            daily_expenses_count = Transaction.objects.filter(
                type='expense',
                created_at__date=transaction_date
            ).exclude(pk=instance.pk).count()

            print(f"DEBUG: Updating expense. Daily count for {transaction_date}: {daily_expenses_count}")

            if daily_expenses_count >= TEST_DAILY_EXPENSE_LIMIT:
                print(f"DEBUG: Daily expense limit of {TEST_DAILY_EXPENSE_LIMIT} reached for {transaction_date} during update.")
                return Response(
                    {'detail': f'Daily expense limit reached ({TEST_DAILY_EXPENSE_LIMIT} expenses per day) for the selected date.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        self.perform_update(serializer)
        print(f"DEBUG: Updated transaction amount: {serializer.instance.amount}, type: {serializer.instance.type}")

        total_balance_after_update, transactions_with_balance_after_update, balance_history_after_update = self._recalculate_balances()
        print("DEBUG: _recalculate_balances total:", total_balance_after_update)

        return Response({
            'total_balance': total_balance_after_update,
            'updated_transaction': serializer.data,
            'transactions': self.get_serializer(transactions_with_balance_after_update[:10], many=True).data,
            'balance_history': balance_history_after_update
        })


    @db_transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)

        total_balance_after_delete, transactions_with_balance_after_delete, balance_history_after_delete = self._recalculate_balances()

        return Response({
            'total_balance': total_balance_after_delete,
            'transactions': self.get_serializer(transactions_with_balance_after_delete[:10], many=True).data,
            'balance_history': balance_history_after_delete
        }, status=status.HTTP_204_NO_CONTENT)


class TransactionListView(TemplateView):
    template_name = 'MoneyTrail/transaction_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['initial_total_balance'] = Decimal('0.00')
        return context

@api_view(['POST'])
def fetch_external_transactions_api(request):
    """
    API endpoint to trigger fetching external transactions.
    """
    try:
        call_command('fetch_transactions', verbosity=1)
        return Response({'detail': 'External transactions fetched successfully.'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'detail': f'Error fetching external transactions: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

