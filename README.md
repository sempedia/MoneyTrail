# 💰 MoneyTrail Transaction Tracker Application

This project is a full-stack web application designed to track financial transactions. It's built with Django (backend), Django REST Framework (API), PostgreSQL (database), and a user-friendly frontend using Bootstrap 5. The entire application is containerized using Docker Compose for easy setup and local development, now simplified with a `Makefile`.

---

## ✨ Features

* **Transaction Management:** Users can **add, view, edit, and delete** local transactions directly through the UI.
* **Running Balance Display:** Shows a running balance for each transaction, calculating the total up to that transaction's date.
* **Current Total Balance:** Displays the overall current balance, dynamically updating with changes.
* **Transaction Import from External API:** Users can import transactions from a mock API into the local database.
* **Manual Transaction Addition:** Users can add new transactions via a Bootstrap modal form.
* **Robust Validations:**
    * Amount must be positive.
    * Adding an expense cannot result in a negative total balance.
    * **Strict Limit of 2 expenses per day.**
* **Pagination:** Loads 10 transactions at a time with a "Load More" option for efficient data display.
* **Basic Filtering:** Users can filter transactions by **type, date range, description (contains), and transaction code (TRN-XXXX)**.
* **Balance Over Time Chart:** Displays a visual representation of the account balance history using **Chart.js**.
* **Responsive UI:** Built with Bootstrap 5 for optimal viewing on various devices.
* **RESTful API:** A robust API built with Django REST Framework for programmatic access to transaction data.
* **PostgreSQL Database:** Reliable and scalable data storage.
* **Dummy Data Generation:** A Django management command (`make fetchdata`) to simulate fetching and saving transactions from an external API (for developer use).
* **Automated Tests:** Comprehensive tests for models, API endpoints, views, and validations.
* **Dockerized:** Easy setup and deployment using Docker and Docker Compose, including robust database startup handling.
* **CI/CD Pipeline (GitHub Actions):** Automated workflows for building, testing, and preparing for deployment.

---

## 🚀 Getting Started

These instructions will get a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Make sure you have Docker and Docker Compose installed on your system.

* **Docker Desktop:** [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)

### Installation and Setup

1.  **Clone the repository:**
    ```bash
    git clone git@github.com:sempedia/MoneyTrail.git
    cd MoneyTrail # Or whatever your project folder name is if you cloned into a different one.
    ```
    *Note: If you already created the `moneytrail_project` directory and copied files, you would instead `cd moneytrail_project` and then initialize git and push to this remote.*

2.  **Configure Environment Variables (`.env` file):**
    This project uses environment variables for sensitive configurations (like database credentials and Django's secret key). An example file, `.env.example`, is provided in the project root.

    * **Create your `.env` file:**
        Copy the example environment variables file to create your local `.env` file:
        ```bash
        cp .env.example .env
        ```
        * You can now open `.env` and modify the values if needed, but the defaults should work for local development.

    * **Generate and Add `SECRET_KEY`:**
        A `SECRET_KEY` is crucial for Django's security. Generate a new one by running this command in your terminal (ensure your virtual environment is active if not using Docker yet for this step):
        ```bash
        python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
        ```
        This command will print a long, random string. Copy this string and paste it as the value for `SECRET_KEY` in your `.env` file. For example:
        ```
        SECRET_KEY=django-insecure-@e3b9p%2$g8v!s*+j&7q-k#f_x1a(z0c)r4y)u5t!i^w!o-l&d=a
        ```
        **Important:** Remember to keep this key secret and never commit your actual `.env` file directly into your version control system (it's already added to `.gitignore`).

    * **PostgreSQL Credentials:**
        The following variables define your PostgreSQL database connection. The default values are set for easy local development with Docker Compose:
        * `POSTGRES_DB=moneytrail_db`
        * `POSTGRES_USER=user`
        * `POSTGRES_PASSWORD=password`
        * `POSTGRES_HOST=db` (This refers to the `db` service name in `docker-compose.yml`)
        * `POSTGRES_PORT=5432`

3.  **Initial Project Setup and Run:**
    Navigate to the root directory of the project (where `Makefile` is located) and run the `install` command. This command also performs necessary database migrations.
    ```bash
    make install
    ```
    The first time you run this, it might take a few minutes as Docker downloads images and builds the application.

4.  **Create a Superuser (for Admin Panel access):**
    ```bash
    make superuser
    ```
    Follow the prompts to create your admin login.

5.  **Populate with Dummy Data (Optional, but recommended for testing):**
    ```bash
    make fetchdata
    ```
    This will import initial transactions from the external API into your local database.

6.  **Access the application:**
    Once the containers are up and running, you can access the application in your web browser at:
    ```
    http://localhost:8000/
    ```
    And the Django Admin panel at:
    ```
    http://localhost:8000/admin/
    ```

---

## ⚙️ Makefile Commands

This project includes a `Makefile` to simplify common development tasks. Ensure you are in the project's root directory to run these commands.

* `make build`: Builds the Docker images for the `web` and `db` services.
* `make up`: Starts Docker containers in detached mode (`-d`).
* `make start`: Starts Docker containers in the foreground (useful for seeing logs directly).
* `make down`: Stops and removes Docker containers (but keeps volumes/data).
* `make down-volumes`: Stops containers and removes associated volumes (your database data will be lost).
* `make install`: Performs initial setup (builds, runs migrations, collects static, starts containers). **Recommended for first-time setup or after `make clean`**.
* `make migrate`: Applies Django database migrations.
* `make makemigrations`: Creates new Django migration files based on model changes.
* `make superuser`: Creates a Django superuser account for the admin panel.
* `make fetchdata`: Runs the custom Django management command to populate the database with dummy transactions from the external API.
* `make test`: Runs all automated tests for the `MoneyTrail` app.
* `make clean`: **Performs a targeted cleanup of Docker resources specific to this project.** This stops containers, removes volumes (data), and removes the Docker image built for this project. It will not affect other Docker containers or images from unrelated projects on your system.

---

## 📊 Daily Workflow Example

1.  **Start the app:** `make up`
2.  **Add dummy data (first time or if needed):** `make fetchdata`
3.  **Access the app:** `http://localhost:8000/`
4.  **Stop the app:** `make down`

---

## 🧪 Running Tests

Automated tests are included to ensure the application's functionality. The test suite is organized into separate files (e.g., `test_models.py`, `test_api.py`) for better readability, maintainability, and focused testing.

* **To run all tests for the `MoneyTrail` app:**
    ```bash
    make test
    ```
    This command will discover and run all tests within the `MoneyTrail/tests/` directory.

* **To run specific test files or classes:**
    You can target specific test files or even individual test classes for faster feedback during development.
    * Run only model tests:
        ```bash
        docker compose exec web python manage.py test MoneyTrail.tests.test_models
        ```
    * Run only API tests:
        ```bash
        docker compose exec web python manage.py test MoneyTrail.tests.test_api
        ```
    * Run only view tests:
        ```bash
        docker compose exec web python manage.py test MoneyTrail.tests.test_views
        ```
    * Run only command tests:
        ```bash
        docker compose exec web python manage.py test MoneyTrail.tests.test_commands
        ```

---

## 🔄 Application Workflow: Backend (DRF) vs. Frontend (JavaScript)

This application follows a common pattern in modern web development where the backend and frontend are separated, communicating via a RESTful API.

### Django REST Framework (DRF): The Backend API Provider

* **Role:** DRF's primary role is to build the **RESTful API** on the Django backend. It handles all server-side logic, database interactions, and data serialization.
* **Key Components:**
    * **Models (`MoneyTrail/models.py`):** Define the structure of your data (e.g., `Transaction` with fields like `api_external_id`, `amount`, `type`, `created_at`).
    * **Serializers (`MoneyTrail/serializers.py`):** Convert complex Django model instances into native Python data types (like dictionaries) that can then be easily rendered into JSON (for sending to the frontend) and vice-versa. They also handle data validation for incoming requests and **add the `display_code` field to the API response**.
    * **ViewSets (`MoneyTrail/views.py` - `TransactionViewSet`):** Provide a set of common operations (Create, Retrieve, Update, Delete - CRUD) for your models. They receive HTTP requests, interact with the database via models, and return responses using serializers. They also contain the custom logic for **running balance calculation, daily expense limits, and balance overspending checks**.
    * **URL Routing (`transaction_tracker/urls.py`):** DRF's `DefaultRouter` automatically generates URL patterns for your API endpoints (e.g., `/api/transactions/` for listing/creating, `/api/transactions/<id>/` for retrieving/updating/deleting a specific transaction).

### JavaScript (in `MoneyTrail/static/MoneyTrail/js/script.js`): The Frontend API Consumer and UI Controller

* **Role:** JavaScript running in the user's web browser is responsible for the entire **user interface (UI)** and dynamic interactions. It does not directly touch the database but communicates with the DRF API.
* **Key Responsibilities:**
    * **Dynamic UI Rendering:** Populates the HTML table with transaction data fetched from the API.
    * **User Interaction Handling:** Listens for user actions (e.g., button clicks for "Add," "Load More," "Load from API," form submissions, **applying filters, clearing filters, clicking Edit/Delete buttons**).
    * **Asynchronous API Calls:** Uses the browser's `fetch` API to send HTTP requests (GET, POST, PUT, DELETE) to the Django REST Framework API endpoints.
    * **UI Updates:** Processes the JSON responses received from the DRF API and updates the HTML page accordingly, often without requiring a full page reload, providing a smoother user experience. This includes **updating the transaction table, the total balance, and rendering/updating the balance over time chart using Chart.js**.

### Workflow Summary:

1.  **Initial Page Load:**
    * User navigates to `http://localhost:8000/`.
    * Django's `TransactionListView` renders `transaction_list.html`.
    * The browser loads HTML, CSS, and `script.js`.
    * `script.js` immediately sends an asynchronous `GET` request to the DRF API endpoint (`/api/transactions/`) to fetch existing transactions, **including historical balance data for the chart**.

2.  **Data Retrieval (GET Request) & Filtering:**
    * The DRF `TransactionViewSet` receives the `GET` request.
    * It applies any active filters (by type, date range, description, or code) from query parameters.
    * It queries the PostgreSQL database for `Transaction` objects, calculates running balances, and applies pagination.
    * `TransactionSerializer` converts these objects into JSON, **adding the `display_code` and `running_balance` fields**.
    * DRF sends the JSON response back to the browser.
    * `script.js` receives the JSON, then uses it to dynamically build and display the transaction table, update the total balance, and **render/update the balance over time chart**.

3.  **User Action (e.g., Adding a Transaction):**
    * User fills out the "Add New Transaction" form in the modal and clicks "Add Transaction."
    * `script.js` captures the form submission event.
    * It collects the form data and constructs a JSON object.
    * `script.js` sends an asynchronous `POST` request to the DRF API endpoint (`/api/transactions/`) with the new transaction's JSON data.

4.  **Data Creation (POST Request) & Validations:**
    * The DRF `TransactionViewSet` receives the `POST` request.
    * `TransactionSerializer` validates the incoming JSON.
    * Custom logic in the `create` method performs additional validations (positive amount, sufficient balance, **daily expense limit of 2 per day**).
    * If validations pass, the new `Transaction` is saved to the PostgreSQL database.
    * DRF sends a `201 Created` HTTP response (including the newly created transaction's data and updated total balance) back to the browser.
    * `script.js` receives the success response, displays a success message, closes the modal, clears the form, and **reloads the transactions (respecting any active filters) and updates the chart** to reflect the changes. If validations fail, it displays the error message in the modal.

5.  **User Action (e.g., Editing a Transaction):**
    * User clicks **"Edit"** next to a transaction, opening a pre-filled modal.
    * User modifies data and clicks "Save Changes."
    * `script.js` sends an asynchronous `PUT` or `PATCH` request to the DRF API endpoint (`/api/transactions/<id>/`) with the updated JSON data.
    * The DRF `TransactionViewSet`'s `update` method processes the request, performs validations (e.g., positive amount, balance check for expenses, **daily expense limit if type/date changes**), and updates the database.
    * On success, `script.js` **reloads the transactions (respecting any active filters) and updates the chart**.

6.  **User Action (e.g., Deleting a Transaction):**
    * User clicks **"Delete"** next to a transaction, opening a confirmation modal.
    * User confirms deletion.
    * `script.js` sends an asynchronous `DELETE` request to the DRF API endpoint (`/api/transactions/<id>/`).
    * The DRF `TransactionViewSet`'s `destroy` method deletes the transaction from the database.
    * On success, `script.js` **reloads the transactions (respecting any active filters) and updates the chart**.

7.  **Importing External Transactions:**
    * User clicks "Load Transactions from API".
    * `script.js` sends a `POST` request to `/api/fetch-external-transactions/`.
    * The `fetch_external_transactions_api` view in Django calls the `fetch_transactions` management command.
    * The command fetches data from `https://685efce5c55df675589d49df.mockapi.io/api/v1/transactions` and saves unique transactions to the database.
    * On success, `script.js` **reloads the transaction list and updates the chart**.

This architecture ensures a clear separation of responsibilities, making the application modular, scalable, and easier to develop and maintain.

---

## 📝 Project Structure


moneytrail_project/
├── env/                       # Your virtual environment (ignored by Git)
├── requirements.txt            # Python dependencies
├── Makefile                    # Simplifies common Docker and Django commands
├── wait_for_it.sh              # Script to wait for services to be ready
├── .github/                    # GitHub Actions workflows
│   └── workflows/
│       └── main.yml            # CI/CD pipeline definition
├── transaction_tracker/        # Django project root (settings, main urls)
│   ├── settings.py             # Django project settings
│   ├── urls.py                 # Main URL router
│   └── wsgi.py                 # WSGI application entry point
├── MoneyTrail/                 # Django app for transaction logic
│   ├── migrations/             # Database schema changes
│   ├── models.py               # Defines the Transaction database model
│   ├── serializers.py          # Django REST Framework serializers for API data
│   ├── views.py                # API ViewSet and frontend view, API for fetching external data
│   ├── urls.py                 # App-specific URL patterns (now minimal)
│   ├── admin.py                # Registers models with Django admin
│   ├── static/                 # Static files for the MoneyTrail app
│   │   └── MoneyTrail/
│   │       ├── css/
│   │       │   └── style.css   # Custom CSS for the frontend
│   │       └── js/
│   │           └── script.js   # Custom JavaScript for frontend logic
│   ├── tests/                  # Directory for automated tests
│   │   ├── init.py         # Makes 'tests' a Python package
│   │   ├── test_models.py      # Tests for the Transaction model
│   │   ├── test_api.py         # Tests for the REST API endpoints
│   │   ├── test_views.py       # Tests for the Django template views
│   │   └── test_commands.py    # Tests for custom management commands
│   └── management/
│       └── commands/
│           └── fetch_transactions.py # Custom command to add dummy data from API
├── templates/                  # Global template directory
│   └── MoneyTrail/
│       ├── base.html                     # Base template for common structure
│       ├── transaction_list.html         # Main page content, extends base.html
│       ├── _add_transaction_modal.html   # Partial: Modal for adding new transactions
│       ├── _edit_transaction_modal.html  # Partial: Modal for editing transactions
│       ├── _delete_confirmation_modal.html # Partial: Modal for confirming deletion
│       └── _message_box_modal.html       # Partial: Custom alert message box
├── .env.example                # Example environment variables file
├── Dockerfile                  # Docker instructions for building the Django app image
├── docker-compose.yml          # Defines and orchestrates Docker services (web, db)
├── README.md                   # This file
└── .gitignore                  # Files/directories to ignore in Git


---

## 💡 Assumptions and Clarifications

* **External API Fetch:** The "Load Transactions from API" button on the UI triggers a Django endpoint that runs the `fetch_transactions` management command. This command fetches data from `https://685efce5c55df675589d49df.mockapi.io/api/v1/transactions`. It handles duplicate `id`s by skipping them.
* **Transaction Code Generation:** For all transactions (both manually added and API imported), the display code will be generated as `TRN-XXXX` where `XXXX` is the zero-padded internal Django `id` of the transaction. The `api_external_id` field is stored for uniqueness but does not directly form the `TRN-XXXX` display code.
* **Amount Handling:** Amounts are stored as positive decimals in the database. The `type` field (`deposit` or `expense`) determines how they are displayed (e.g., `+$X.XX` or `-$X.XX`) and how they affect the running balance.
* **Running Balance Calculation:** The running balance is calculated on the backend within the `TransactionViewSet`'s `_recalculate_balances` method. This method internally orders all transactions chronologically (oldest to newest) to ensure correct running balance calculation. The final list returned to the frontend is then reversed (newest to oldest). **The overall `total_balance` is calculated by summing all transactions directly from the database to ensure accuracy.**
* **Pagination:** Basic pagination (10 items per page) is implemented. The "Load More" button fetches the next page from the database.
* **Authentication:** For simplicity and to meet the core requirements, the API endpoints are publicly accessible (`AllowAny` permission in DRF settings). In a production application, you would implement proper authentication and authorization (e.g., Token Authentication, JWT).
* **Frontend Scope:** The frontend provides core CRUD operations (Create, Read, Update, Delete).
* **Error Handling (Frontend):** Server-side validation errors and general API errors are displayed in the modal or a message box.
* **Static Files (Development vs. Production):** While CDNs are used for external libraries in development for convenience, for production deployments, it's recommended to serve all static files (including Bootstrap, etc.) locally after running `collectstatic`.
* **Docker Compose Command:** The `command` in `docker-compose.yml` is now simplified to only run the Django server, as `makemigrations`, `migrate`, and `collectstatic` are handled by the `make install` command.

---

## 🤝 Contributing

Feel free to fork this repository, open issues, or submit pull requests with improvements.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🧑‍💻 Author

* Alina Bazavan - [GitHub Profile](https://github.com/sempedia)
