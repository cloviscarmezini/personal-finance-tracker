# Personal Finance Tracker
**CS50’s Web Development with Python and JavaScript - Capstone Project**

## Overview
Personal Finance Tracker is a comprehensive, full-stack financial management web application built using Django and modern JavaScript. The platform empowers users to take full control of their financial health by tracking multi-currency transactions, managing diverse digital wallets, establishing dynamic monthly spending budgets, and analyzing real-time financial flows through an interactive visualization dashboard.

## Distinctiveness and Complexity

This project satisfies and exceeds the distinctiveness and complexity requirements outlined in the CS50 Capstone specifications through its highly specific domain focus, enterprise-level software architecture, and seamless integration of external services.

**Distinctiveness:**
This application operates strictly within the financial technology (FinTech) domain. It is a dedicated Personal Finance Management Platform that requires complex, domain-specific logic. The system processes real-time consolidation of user assets across accounts operating in entirely different currencies (e.g., USD, BRL, EUR) by automatically applying dynamic exchange rates. Furthermore, it features an intelligent budget-tracking engine that computes monthly spending limits per category, triggering real-time threshold calculations as the user inputs new transactions. The data is then synthesized into an advanced ledger querying system that isolates monthly performance while allowing instantaneous multi-parameter filtering. 

**Complexity:**
The complexity of this project lies in its departure from standard, basic Django implementations. Instead of placing business logic directly inside views or templates, this application enforces a clean **Layered Architecture (Separation of Concerns)** to ensure high maintainability and testability:
* **Service Layer Pattern:** All core business computations, validation rules, and ledger manipulations reside strictly inside isolated Service classes.
* **Data Transfer Objects (DTOs) & Mappers:** Communication between presentation views and business services is decoupled using explicit DTO classes and Mapper utilities, preventing the direct exposure of database models to the frontend.
* **External API Client Integration:** The backend features a custom HTTP Client (`ExchangeClient`) built with robust error handling and fallback mechanisms to consume live third-party currency exchange APIs.
* **Asynchronous Frontend:** The user interface relies heavily on asynchronous JavaScript (`fetch` API). Actions like logging transactions, calculating balance updates, switching base currencies, and re-rendering `Chart.js` graphs happen dynamically without requiring full page reloads, providing a smooth, single-page application (SPA) feel.

---

## File and Directory Structure Write-up

Below is a comprehensive write-up of every significant file contributed to this project, detailing its purpose and contents:

### Presentation Layer (Views)
* `finance/views/auth_view.py`: Manages user authentication workflows, including registration, login validation, session termination, and the rendering of authentication forms.
* `finance/views/dashboard_view.py`: Serves as the primary controller for the home screen. It aggregates consolidated net worth, wallet breakdowns, current monthly expenses, and active budget thresholds by invoking service classes, passing the formatted data to the dashboard template.
* `finance/views/transaction_view.py`: Contains the logic for rendering the transaction ledger, processing the creation of new financial entries, and handling updates or deletion requests.
* `finance/views/wallet_view.py`: Handles HTTP requests for listing active wallets, creating new accounts, editing wallet details (name, currency), and managing wallet archiving.
* `finance/views/category_view.py`: Controls the views for displaying, creating, and editing custom spending classifications, including their visual properties (icons and colors).
* `finance/views/budget_view.py`: Manages the interfaces for setting monthly category spending caps and querying current spending progress against assigned budgets.
* `finance/views/api_views.py`: Exposes lightweight JSON API endpoints designed explicitly for frontend JavaScript fetch requests (e.g., dynamic chart data updates and real-time balance checks).

### Business Logic Layer (Services)
* `finance/services/base_service.py`: An abstract base class providing shared utilities, database error handling, and generic CRUD query helpers inherited by other services.
* `finance/services/transaction_service.py`: Encapsulates the core rules for financial movements. Validates entries, updates target wallet balances, and processes complex filtering queries.
* `finance/services/wallet_service.py`: Manages wallet domain logic, including balance recalculations based on historical entries and total user asset valuation.
* `finance/services/category_service.py`: Handles category domain management, enforcing unique naming constraints and assigning default icons/colors.
* `finance/services/budget_service.py`: Calculates monthly category usage by aggregating expenses within specific timeframes and evaluating them against user caps.
* `finance/services/exchange_service.py`: Orchestrates currency conversion logic, interacting with the client to retrieve rates and handle fallback math when APIs are unavailable.

### External Integration & Data Transfer
* `finance/clients/exchange_client.py`: A dedicated HTTP API client for making outgoing requests to the ExchangeRate-API. Includes strict error catching and graceful fallbacks.
* `finance/dtos/` (`transaction_dto.py`, `wallet_dto.py`, `budget_dto.py`): Define immutable data structures used to transfer information securely between views and services.
* `finance/mappers/` (`transaction_mapper.py`, `wallet_mapper.py`, `budget_mapper.py`): Utility classes responsible for converting Django ORM model instances into their respective DTO structures and vice versa.

### Models & Commands
* `finance/models.py`: Defines the relational database schema using Django ORM. Contains the `User`, `Wallet`, `Category`, `Transaction`, and `Budget` models with their respective relationships and constraints.
* `finance/management/commands/seed_categories.py`: A custom Django command to pre-populate the database with default system categories (e.g., Housing, Food, Transport) utilizing predefined Bootstrap icons and hex colors.
* `finance/management/commands/seed_ledger.py`: A developer utility to populate sample wallet balances and mock transactions for initial testing.

### Frontend (Templates & Static Assets)
* `finance/templates/finance/layout.html`: The master HTML layout containing the global navigation sidebar, dynamic headers, and script imports.
* `finance/templates/finance/dashboard.html`: The core view displaying net worth summary cards, Chart.js canvases, and budget progress bars.
* `finance/templates/finance/manage_transactions.html`: The interactive ledger interface equipped with filter controls and pagination.
* `finance/templates/finance/manage_wallets.html`, `manage_categories.html`, `manage_budgets.html`: Dedicated templates providing CRUD forms and tables for system resources.
* `finance/templates/finance/includes/`: Contains reusable HTML snippets and modals (`transaction_modal.html`, `wallet_modal.html`, `currency_modal.html`).
* `finance/static/finance/css/index.css`: Custom stylesheet overriding Bootstrap defaults, styling the sidebar, dashboard cards, and overall responsive layout.
* `finance/static/finance/js/finance.js`: The main JavaScript file handling asynchronous form submissions, modal events, DOM manipulation, and Chart.js rendering.
* `finance/static/finance/js/shared.js`: Helper script providing shared functions for currency formatting, date parsing, and UI alerts.

---

## Environment Variables Setup

The application uses environment variables for security and external API configurations. You can optionally create a `.env` file in the root directory based on the following variables:

    SECRET_KEY=your_custom_django_secret_key
    DEBUG=True
    EXCHANGE_RATE_API_KEY=your_exchange_api_key_here

### Automatic Fallbacks & Default Configuration
To ensure zero-configuration setup for local evaluation and testing, **all environment variables feature built-in fallbacks**:
* **`SECRET_KEY`**: Uses a default development key if not supplied.
* **`DEBUG`**: Defaults to `True` for development convenience.
* **`EXCHANGE_RATE_API_KEY`**: If no API key is provided, the `ExchangeClient` gracefully falls back to mock conversion rates, ensuring all dashboard features continue to function seamlessly.

---

## How to Run the Application

1.  **Prerequisites**: Ensure that you have Python 3.10+ installed.
2.  **Install Dependencies**: Navigate to the project root and install requirements:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  **Database Setup**: Apply migrations to create the SQLite database:
    ```bash
    python manage.py makemigrations finance
    python manage.py migrate
    ```
4.  **Seed the Database (Recommended)**: Generate initial default categories:
    ```bash
    python manage.py seed_categories
    ```
5.  **Start the Server**:
    ```bash
    python manage.py runserver
    ```
6.  **Access**: Open `http://127.0.0.1:8000/` and register a new account to begin.

---

## Academic Honesty & Credits
* **Author:** Clovis Carmezini (Junior)
* **Course:** CS50’s Web Development with Python and JavaScript (HarvardX)
* **edX Username:** `cloviscarmezini`
* **GitHub:** [`@cloviscarmezini`](https://github.com/cloviscarmezini)
