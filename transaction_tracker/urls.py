"""
URL configuration for transaction_tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from MoneyTrail.views import TransactionViewSet, TransactionListView, fetch_external_transactions_api

# Create a router for your API views
router = routers.DefaultRouter()
router.register(r'transactions', TransactionViewSet) # Register the TransactionViewSet with the router

urlpatterns = [
    path('admin/', admin.site.urls),
    # Map the root URL ('/') to the MoneyTrail app's TransactionListView
    # This will serve your HTML frontend at http://localhost:8000/
    path('', TransactionListView.as_view(), name='transaction_list'),
    # Include the API URLs under the 'api/' prefix
    # This will serve your API at http://localhost:8000/api/transactions/
    path('api/', include(router.urls)),
    # Endpoint for user to trigger fetching external transactions
    path('api/fetch-external-transactions/', fetch_external_transactions_api, name='fetch_external_transaction_api'),
    # You might also want to include DRF's browsable API login/logout
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),]
