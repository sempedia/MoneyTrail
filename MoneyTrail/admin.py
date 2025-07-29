from django.contrib import admin
from .models import Transaction

# Register your models here.

# We register the Transaction model with the Django admin site.
# This makes the Transaction model visible and manageable in the admin interface.
# Once registered, you can go to /admin/ and log in to see and manage your transactions.
admin.site.register(Transaction)
