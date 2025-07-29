document.addEventListener('DOMContentLoaded', function() {
    const transactionsTableBody = document.getElementById('transactionsTableBody');
    const totalBalanceDisplay = document.getElementById('totalBalanceDisplay');
    const loadApiTransactionsBtn = document.getElementById('loadApiTransactionsBtn');
    const addTransactionForm = document.getElementById('addTransactionForm');
    const addTransactionModal = new bootstrap.Modal(document.getElementById('addTransactionModal'));
    const addTransactionError = document.getElementById('addTransactionError');
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    const emptyState = document.getElementById('emptyState');

    // Filter Elements
    const filterType = document.getElementById('filterType');
    const filterStartDate = document.getElementById('filterStartDate');
    const filterEndDate = document.getElementById('filterEndDate');
    const filterDescription = document.getElementById('filterDescription');
    const filterCode = document.getElementById('filterCode');
    const applyFiltersBtn = document.getElementById('applyFiltersBtn');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');

    // Chart Elements
    const balanceChartCanvas = document.getElementById('balanceChart');
    let chartInstance = null; // To hold the Chart.js instance

    // Edit Modal Elements
    const editTransactionModal = new bootstrap.Modal(document.getElementById('editTransactionModal'));
    const editTransactionForm = document.getElementById('editTransactionForm');
    const editTransactionId = document.getElementById('editTransactionId');
    const editTransactionCode = document.getElementById('editTransactionCode');
    const editTransactionDescription = document.getElementById('editTransactionDescription');
    const editTransactionAmount = document.getElementById('editTransactionAmount');
    const editTransactionDate = document.getElementById('editTransactionDate');
    const editTransactionType = document.getElementById('editTransactionType');
    const editTransactionError = document.getElementById('editTransactionError');

    // Delete Modal Elements
    const deleteConfirmationModal = new bootstrap.Modal(document.getElementById('deleteConfirmationModal'));
    const deleteTransactionId = document.getElementById('deleteTransactionId');
    const deleteTransactionCodeDisplay = document.getElementById('deleteTransactionCodeDisplay');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');


    let currentPage = 1;
    let hasMorePages = true;
    let activeFilters = {}; // Object to store current filter parameters

    // Function to fetch transactions from the API (your Django backend)
    async function fetchTransactions(page = 1, filters = {}) {
        try {
            const queryParams = new URLSearchParams();
            queryParams.append('page', page);

            for (const key in filters) {
                if (filters[key]) {
                    queryParams.append(key, filters[key]);
                }
            }

            const response = await fetch(`/api/transactions/?${queryParams.toString()}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error fetching transactions:', error);
            showMessageBox('Error', 'Failed to load transactions. Please try again.', true);
            return null;
        }
    }

    // Function to render transactions in the table
    function renderTransactions(transactions, append = false) {
        if (!append) {
            transactionsTableBody.innerHTML = '';
        }

        if (transactions.length === 0 && !append) {
            emptyState.style.display = 'block';
            loadMoreBtn.style.display = 'none';
            return;
        } else {
            emptyState.style.display = 'none';
        }

        transactions.forEach(transaction => {
            const row = transactionsTableBody.insertRow();
            row.insertCell().textContent = transaction.display_code || 'N/A';
            row.insertCell().textContent = transaction.description || '-';

            const amountValue = parseFloat(transaction.amount);
            const amountCell = row.insertCell();
            const displayAmount = transaction.type === 'expense' ? `-$${amountValue.toFixed(2)}` : `+$${amountValue.toFixed(2)}`;
            amountCell.textContent = displayAmount;
            amountCell.classList.add(transaction.type === 'expense' ? 'text-danger' : 'text-success');

            row.insertCell().textContent = new Date(transaction.created_at).toLocaleDateString();
            row.insertCell().textContent = transaction.type.charAt(0).toUpperCase() + transaction.type.slice(1);

            const runningBalanceValue = parseFloat(transaction.running_balance);
            const runningBalanceCell = row.insertCell();
            runningBalanceCell.textContent = `$${runningBalanceValue.toFixed(2)}`;
            runningBalanceCell.classList.add(runningBalanceValue < 0 ? 'text-danger' : 'text-success');

            const actionsCell = row.insertCell();
            actionsCell.classList.add('actions-cell');

            const editBtn = document.createElement('button');
            editBtn.className = 'btn btn-sm btn-info rounded-pill';
            editBtn.innerHTML = '<i class="fas fa-edit"></i> Edit';
            editBtn.dataset.transactionId = transaction.id;
            editBtn.dataset.displayCode = transaction.display_code;
            editBtn.dataset.description = transaction.description;
            editBtn.dataset.amount = transaction.amount;
            editBtn.dataset.date = new Date(transaction.created_at).toISOString().split('T')[0];
            editBtn.dataset.type = transaction.type;
            editBtn.addEventListener('click', openEditModal);
            actionsCell.appendChild(editBtn);

            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'btn btn-sm btn-danger rounded-pill';
            deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i> Delete';
            deleteBtn.dataset.transactionId = transaction.id;
            deleteBtn.dataset.displayCode = transaction.display_code;
            deleteBtn.addEventListener('click', openDeleteModal);
            actionsCell.appendChild(deleteBtn);
        });
    }

    // Function to update the total balance display
    function updateBalanceDisplay(balance) {
        const balanceValue = parseFloat(balance);
        totalBalanceDisplay.textContent = `$${balanceValue.toFixed(2)}`;
        if (balanceValue < 0) {
            totalBalanceDisplay.classList.remove('text-success');
            totalBalanceDisplay.classList.add('text-danger');
        } else {
            totalBalanceDisplay.classList.remove('text-danger');
            totalBalanceDisplay.classList.add('text-success');
        }
    }

    // Function to update the chart
    function updateChart(balanceHistory) {
        // Prepare data for Chart.js
        const labels = balanceHistory.map(item => item.date);
        const data = balanceHistory.map(item => item.balance);

        if (chartInstance) {
            chartInstance.destroy(); // Destroy existing chart instance if it exists
        }

        chartInstance = new Chart(balanceChartCanvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Balance Over Time',
                    data: data,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, // Allow canvas to resize freely
                scales: {
                    x: {
                        type: 'time', // Use 'time' scale for dates
                        time: {
                            unit: 'day',
                            tooltipFormat: 'MMM D, YYYY',
                            displayFormats: {
                                day: 'MMM D'
                            }
                        },
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        beginAtZero: true, // Start Y-axis at 0
                        title: {
                            display: true,
                            text: 'Balance ($)'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Balance: $${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Initial load of transactions (now considers activeFilters and updates chart)
    async function loadInitialTransactions() {
        currentPage = 1;
        const data = await fetchTransactions(currentPage, activeFilters);
        if (data) {
            renderTransactions(data.transactions);
            updateBalanceDisplay(data.total_balance);
            hasMorePages = data.has_more;
            loadMoreBtn.style.display = hasMorePages ? 'block' : 'none';
            updateChart(data.balance_history); // Update the chart with historical data
        }
    }

    // Event listener for "Load More" button (now considers activeFilters and updates chart)
    loadMoreBtn.addEventListener('click', async () => {
        if (hasMorePages) {
            loadMoreBtn.disabled = true;
            loadMoreBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';

            currentPage++;
            const data = await fetchTransactions(currentPage, activeFilters);
            if (data) {
                renderTransactions(data.transactions, true);
                hasMorePages = data.has_more;
                loadMoreBtn.style.display = hasMorePages ? 'block' : 'none';
                // Chart is only updated on initial load, not subsequent loads,
                // as it shows overall history. If filters are applied, chart
                // updates on 'Apply Filters' click.
            }
            loadMoreBtn.disabled = false;
            loadMoreBtn.innerHTML = 'Load More';
        }
    });

    // Event listener for "Load Transactions from API" button
    loadApiTransactionsBtn.addEventListener('click', async () => {
        loadApiTransactionsBtn.disabled = true;
        loadApiTransactionsBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
        try {
            const response = await fetch('/api/fetch-external-transactions/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            showMessageBox('Success', 'Transactions imported from external API!');
            loadInitialTransactions(); // Reload all transactions and update chart
        } catch (error) {
            console.error('Error importing transactions:', error);
            showMessageBox('Error', `Failed to import transactions: ${error.message}`, true);
        } finally {
            loadApiTransactionsBtn.disabled = false;
            loadApiTransactionsBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Load Transactions from API';
        }
    });


    // Event listener for "Add Transaction" form submission
    addTransactionForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        addTransactionError.style.display = 'none';

        const description = document.getElementById('transactionDescription').value;
        const amount = parseFloat(document.getElementById('transactionAmount').value);
        const date = document.getElementById('transactionDate').value;
        const type = document.getElementById('transactionType').value;

        if (isNaN(amount) || amount <= 0) {
            addTransactionError.textContent = 'Amount must be a positive number.';
            addTransactionError.style.display = 'block';
            return;
        }
        if (!description.trim()) {
            addTransactionError.textContent = 'Description cannot be empty.';
            addTransactionError.style.display = 'block';
            return;
        }
        if (!date) {
            addTransactionError.textContent = 'Date cannot be empty.';
            addTransactionError.style.display = 'block';
            return;
        }

        const currentTotalBalanceText = totalBalanceDisplay.textContent.replace('$', '').trim();
        const currentTotalBalance = parseFloat(currentTotalBalanceText);

        if (isNaN(currentTotalBalance)) {
            addTransactionError.textContent = 'Error: Could not read current balance for validation.';
            addTransactionError.style.display = 'block';
            console.error('Failed to parse current total balance:', totalBalanceDisplay.textContent);
            return;
        }

        if (type === 'expense' && amount > currentTotalBalance) {
            addTransactionError.textContent = 'Not enough balance. Cannot add expense.';
            addTransactionError.style.display = 'block';
            return;
        }

        const transactionData = {
            description: description,
            amount: amount,
            created_at: date,
            type: type
        };

        try {
            const response = await fetch('/api/transactions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(transactionData)
            });

            const data = await response.json();

            if (!response.ok) {
                let errorMessage = 'Failed to add transaction.';
                if (data.detail) {
                    errorMessage = data.detail;
                } else if (data.amount) {
                    errorMessage = `Amount error: ${data.amount.join(', ')}`;
                } else if (data.type) {
                    errorMessage = `Type error: ${data.type.join(', ')}`;
                } else if (data.description) {
                    errorMessage = `Description error: ${data.description.join(', ')}`;
                } else if (data.created_at) {
                    errorMessage = `Date error: ${data.created_at.join(', ')}`;
                }
                addTransactionError.textContent = errorMessage;
                addTransactionError.style.display = 'block';
            } else {
                showMessageBox('Success', 'Transaction added successfully!');
                addTransactionModal.hide();
                addTransactionForm.reset();
                loadInitialTransactions(); // Reload transactions and update chart
            }
        } catch (error) {
            console.error('Error adding transaction:', error);
            addTransactionError.textContent = 'An unexpected error occurred. Please try again.';
            addTransactionError.style.display = 'block';
        }
    });

    // Function to open the Edit Transaction Modal
    function openEditModal(event) {
        const btn = event.currentTarget;
        editTransactionId.value = btn.dataset.transactionId;
        editTransactionCode.value = btn.dataset.displayCode;
        editTransactionCode.setAttribute('readonly', true);
        editTransactionDescription.value = btn.dataset.description;
        editTransactionAmount.value = btn.dataset.amount;
        editTransactionDate.value = btn.dataset.date;
        editTransactionType.value = btn.dataset.type;
        editTransactionError.style.display = 'none';
        editTransactionModal.show();
    }

    // Event listener for Edit Transaction form submission
    editTransactionForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        editTransactionError.style.display = 'none';

        const id = editTransactionId.value;
        const description = editTransactionDescription.value;
        const amount = parseFloat(editTransactionAmount.value);
        const date = editTransactionDate.value;
        const type = editTransactionType.value;

        if (isNaN(amount) || amount <= 0) {
            editTransactionError.textContent = 'Amount must be a positive number.';
            editTransactionError.style.display = 'block';
            return;
        }
        if (!description.trim()) {
            editTransactionError.textContent = 'Description cannot be empty.';
            editTransactionError.style.display = 'block';
            return;
        }
        if (!date) {
            editTransactionError.textContent = 'Date cannot be empty.';
            editTransactionError.style.display = 'block';
            return;
        }

        const transactionData = {
            description: description,
            amount: amount,
            created_at: date,
            type: type
        };

        try {
            const response = await fetch(`/api/transactions/${id}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(transactionData)
            });

            const data = await response.json();

            if (!response.ok) {
                let errorMessage = 'Failed to update transaction.';
                if (data.detail) {
                    errorMessage = data.detail;
                } else if (data.amount) {
                    errorMessage = `Amount error: ${data.amount.join(', ')}`;
                } else if (data.type) {
                    errorMessage = `Type error: ${data.type.join(', ')}`;
                } else if (data.description) {
                    errorMessage = `Description error: ${data.description.join(', ')}`;
                } else if (data.created_at) {
                    errorMessage = `Date error: ${data.created_at.join(', ')}`;
                }
                editTransactionError.textContent = errorMessage;
                editTransactionError.style.display = 'block';
            } else {
                showMessageBox('Success', 'Transaction updated successfully!');
                editTransactionModal.hide();
                loadInitialTransactions(); // Reload transactions and update chart
            }
        } catch (error) {
            console.error('Error updating transaction:', error);
            editTransactionError.textContent = 'An unexpected error occurred. Please try again.';
            editTransactionError.style.display = 'block';
        }
    });

    // Function to open the Delete Confirmation Modal
    function openDeleteModal(event) {
        const btn = event.currentTarget;
        deleteTransactionId.value = btn.dataset.transactionId;
        deleteTransactionCodeDisplay.textContent = btn.dataset.displayCode;
        deleteConfirmationModal.show();
    }

    // Event listener for Confirm Delete button
    confirmDeleteBtn.addEventListener('click', async () => {
        const id = deleteTransactionId.value;
        try {
            const response = await fetch(`/api/transactions/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            showMessageBox('Success', 'Transaction deleted successfully!');
            deleteConfirmationModal.hide();
            loadInitialTransactions(); // Reload transactions and update chart
        } catch (error) {
            console.error('Error deleting transaction:', error);
            showMessageBox('Error', `Failed to delete transaction: ${error.message}`, true);
        }
    });

    // Event listeners for filter buttons
    applyFiltersBtn.addEventListener('click', () => {
        activeFilters = {
            type: filterType.value,
            start_date: filterStartDate.value,
            end_date: filterEndDate.value,
            description_search: filterDescription.value,
            code_search: filterCode.value
        };
        loadInitialTransactions(); // Reload transactions with new filters and update chart
    });

    clearFiltersBtn.addEventListener('click', () => {
        filterType.value = '';
        filterStartDate.value = '';
        filterEndDate.value = '';
        filterDescription.value = '';
        filterCode.value = '';
        activeFilters = {};
        loadInitialTransactions(); // Reload all transactions and update chart
    });


    // Function to get CSRF token from cookies (required for Django POST/PUT/DELETE requests)
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Initialize the page
    loadInitialTransactions();
});
