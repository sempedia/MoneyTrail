from django.test import TestCase
from django.urls import reverse
from rest_framework import status

# Test for our Django Template View
class TransactionListViewTest(TestCase):
    # Test if the transaction list page loads successfully.
    def test_transaction_list_view(self):
        # Use reverse to get the URL for our 'transaction_list' view.
        url = reverse('transaction_list')
        response = self.client.get(url)
        # Check if the response status code is 200 OK.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if the correct template was used to render the page.
        self.assertTemplateUsed(response, 'MoneyTrail/transaction_list.html')
        # Check if the page content contains a specific string, indicating it loaded correctly.
        self.assertContains(response, "MoneyTrail Transaction Tracker")


