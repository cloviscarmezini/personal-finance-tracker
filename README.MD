# GlobalFinance: Personal SaaS Wealth & Multi-Currency Tracker

## Project Overview
GlobalFinance is a comprehensive, mobile-responsive Personal Finance Management SaaS built with Django and vanilla JavaScript. Designed to meet the demands of modern global citizens, freelancers, and investors, the platform allows users to manage multiple wallets across different currencies seamlessly. 

The core architecture leverages a decoupled Python service layer for backend ledger processing with dynamic asynchronous front-end updates, delivering a Single Page Application (SPA) experience where crucial. A signature feature of the application is its live integration with the external ExchangeRate-API, which aggregates currency valuations on the fly using strict `Decimal` precision to provide users with a consolidated, real-time view of their global net worth.

---

## Technical Complexity & Architecture Justification
This application substantially transcends the scope of previous course projects by combining advanced relational database designs, multi-user role isolation, third-party RESTful API consumption, and complex data aggregations. 

Steering away from standard monolithic Django implementations, GlobalFinance implements an advanced software design pattern inspired by modern enterprise conventions, cleanly separating concerns using a variation of the **Service Layer** and **CQRS (Command Query Responsibility Segregation)** principles:

*   **Infrastructure Isolation:** Encapsulates outbound HTTP requests, timeout vectors, and fallback routing using native `Decimal` conversions to eliminate binary floating-point round-off errors.
*   **Domain Services (Commands):** All write operations, resource mutations (CRUD), database transactions (`@db_transaction.atomic`), and automation routines live inside dedicated pure Python operations.
*   **Domain Selectors (Queries):** Complex database aggregates (`Sum`, `Count`), historical analytical tracking, and calculations live in a highly performant, read-only layer optimized for client data serialization.

This architecture removes code bloat from the presentation layer (`views.py`), ensuring maximum scalability, weak coupling, and highly professional code cohesion.

---

## Features and Deep-Dive Explanation

### 1. Dynamic Multi-Currency Wallets (Core Architecture)
Users can create and isolate separate "Wallets" mapped to distinct global currencies (e.g., BRL, USD, and EUR). Each wallet tracks its individual ledger independently. Clicking on any wallet card inside the main Dashboard automatically routes the user to the ledger view, pre-filtering all entries by that specific asset.

### 2. Live ExchangeRate-API Integration & Automated Currency Conversion
When a user inputs a transaction into a non-primary currency wallet, the domain service captures the payload and dispatches a synchronous call via the unified `ExchangeRateClient`. The system fetches the exact real-time conversion multiplier, converts the transaction amount into the user's primary base currency, and persists both the original foreign value and the base-converted equivalent into the SQL database layer.

### 3. Consolidated Net Worth Dashboard
The main entry point features a high-impact analytical header that aggregates the current balances of all active wallets. By leveraging the Domain Selector layer, the platform dynamically computes and sums up all foreign asset values into the user's chosen base currency on the fly, rendering a unified "Global Net Worth" metric upon login.

### 4. Interactive Analytics & Data Visualization (Chart.js SPA Pipelines)
To avoid heavy page-refresh cycles, the transaction history is aggregated via customized selectors and serialized into lightweight JSON arrays. The front-end captures this data through asynchronous `Fetch` requests and hooks into the **Chart.js** library via CDN. It renders real-time animated doughnut charts for category distributions (e.g., Housing vs. Food).

### 5. Robust Multi-Tiered Transaction Ledger & Custom Query Filters
A comprehensive transaction tracking system supporting paginated historical data via a dedicated view. Users can query their financial history using advanced filters that dynamically alter the URL query string, slicing ledger logs by active wallet, date range, spending category (including dedicated grouping for **Uncategorized** entries), and value intervals (Min/Max amount). It also supports explicit ordering matrices (Highest/Lowest amount, Newest/Oldest creation date).

### 6. Modular SPA Transaction Creation
To maximize UX accessibility while respecting the **DRY** principle, transaction logging is componentized into a single reusable modal template block (`_transaction_modal.html`). When triggered from the Dashboard, it performs its core routing; when triggered from the Transactions Ledger, it intercepts the submit event via JavaScript, pushes the record to the backend, and injects the new row dynamically into the active HTML table without forcing a full page reload. It also dynamically pre-selects the active wallet if a ledger filter is currently engaged.

### 7. Global Category Seeder & Safe Reseed Pipeline
Includes a customized database initialization CLI command (`python manage.py seed_categories`) to populate system-wide core default financial categories. Furthermore, the Category Manager features an explicit **"Reset to Defaults"** atomic pipeline. When triggered, it safely wipes user-customized category relations and re-clones system defaults from the global matrix.

### 8. Strict Data Integrity & Cascade Constraints
The relational database layer enforces production-grade business boundaries to protect ledger history:
*   **User Erasure:** Deleting a user profile triggers a complete `CASCADE` wipe across all associated wallets, categories, transactions, and budgets.
*   **Wallet Erasure:** Removing an active wallet purges all transaction rows contained inside that ledger (`CASCADE`).
*   **Category Erasure:** Deleting an expense category triggers an explicit `on_delete=models.SET_NULL` on the transactions log. Financial records are never lost; their metrics are simply grouped under a fallback **"Uncategorized"** label and automatically tracked via a neutral visual block in the selector layer. Budgets associated with a removed category are completely dropped (`CASCADE`).

### 9. Automated Recurring Transactions Pipeline
Designed to manage fixed monthly contracts, subscriptions, or recurring bills without running resource-heavy external background daemons. The system integrates a lightweight service hook during the user authentication cycle: upon a successful login event, Django cross-checks scheduled recurring models against the current date matrix and clones pending transactions smoothly into the active ledger database.

### 10. Native PDF Financial Statement Generator
Users can export clean, print-ready, professionally formatted financial statements summarizing monthly closings. 
*Note: This feature is handled with optimal developer efficiency by styling the DOM layout via native CSS media print directives (`@media print`), enabling users to generate clean PDFs natively via the browser engine at zero server performance overhead.*

---

## File Structure & App Architecture

*   `config/`: Project configuration root containing system-wide architectural mappings, routing paths, and environment initialization (`settings.py`, `urls.py`).
*   `finance/models.py`: Defines the relational database schemas for `User`, `Wallet`, `Category`, `Transaction`, and `Budget`, managing advanced relational cascades and constraints.
*   `finance/services.py`: Implements the core unified Domain Business Logic, external API client operations (`ExchangeRateClient`), write commands, atomic resource mutations, and category re-seed operations.
*   `finance/selectors.py`: Houses pure, read-only data extraction queries, computing global net worth metrics, grouping uncategorized entries, and formatting data payloads for client consumption.
*   `finance/management/commands/seed_categories.py`: Custom Django management CLI command providing idempotent seeding routines for system-wide defaults.
*   `finance/views.py`: Acts purely as a thin interface layer, capturing incoming HTTP/AJAX protocols, delegating tasks to services/selectors, and returning presentation or JSON results.
*   `finance/static/finance/js/finance.js`: Handles event delegation for asynchronous form submissions, intercepting transaction modal entries for SPA updates, dynamic progress bar mutations, and Chart.js instantiation.
*   `finance/templates/finance/`: Contains the modular HTML templates extending a centralized responsive layout, alongside componentized includes (`includes/_pagination.html`, `includes/_transaction_modal.html`).

---

## Environment Security & Requirements
To conform with modern enterprise production standards, this application implements strict data security boundaries. Sensitive configurations, including Django infrastructure secrets and API environment variables, are completely externalized from the source code via environment variable parsing.

*   `requirements.txt`: Manages production-level core dependencies (`Django`, `requests`, `python-dotenv`).
*   `.env`: Local runtime environment mapping file containing credentials. (Safeguarded from source control repositories via `.gitignore`).

---

## How to Run the Application Locally

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd globalfinance

2. **Set up a virtual environment and install dependencies:**

   ```python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

3. **Configure environment variables:**
   ```SECRET_KEY=your_django_secret_key_here
      EXCHANGE_RATE_API_KEY=your_exchangerate_api_key_here

4. **Run database migrations and configure schema boundaries:**
   ```python manage.py makemigrations finance
      python manage.py migrate

5. **Seed the global system categories into the database:**
   ```python manage.py seed_categories

6. **Start the local development environment server:**
   ```python manage.py runserver
   