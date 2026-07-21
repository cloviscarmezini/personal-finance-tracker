# CS50 Web Capstone: Personal Finance Tracker

## Overview
This project is a personal finance management web application built with Django. The system allows users to log transactions, manage multiple wallets, establish budgets, and categorize their income and expenses. Additionally, the application provides an interactive dashboard for financial data analysis and visualization.

## Distinctiveness and Complexity
This project fully satisfies the distinctiveness and complexity requirements for the CS50 Web Capstone for the following reasons:

*   **Domain Distinctiveness:** This application is strictly a financial management tool. It is neither a social network nor an e-commerce platform, ensuring it is completely distinct from the other projects in the course.
*   **Layered Architecture:** Unlike conventional, basic Django projects that place all logic inside views, this system implements a robust separation of concerns. It introduces DTOs (Data Transfer Objects), Mappers, Services, and Clients. This architecture completely isolates business logic from the presentation layer (Views), making the codebase highly scalable, testable, and maintainable.
*   **External Integrations:** The project features a custom HTTP client (`exchange_client.py` and `exchange_service.py`) to handle communication with external currency exchange APIs, allowing for dynamic currency conversions and data integration.
*   **Dynamic Front-End and Data Visualization:** The front-end leverages Bootstrap and custom JavaScript, integrated heavily with `Chart.js` to render interactive financial graphs on the Dashboard. The UI also relies on dynamic modals for quick transaction entries and currency exchanges without requiring full page reloads.
*   **Custom Management Scripts:** Custom Django management commands (`seed_categories.py` and `seed_ledger.py`) were developed to automatically populate the database with default categories and sample transactions, significantly streamlining the initial setup process.

---

## File and Directory Structure

Below is a detailed breakdown of the main components and directories created for this application:

### 1. Presentation Layer (Views)
The `finance/views/` directory was modularized to organize routing logic effectively:
*   **`auth_view.py`**: Handles user registration, login, and logout processes.
*   **`dashboard_view.py`**: Prepares and aggregates financial metrics and graph data for the home screen.
*   **`transaction_view.py`, `wallet_view.py`, `budget_view.py`, `category_view.py`**: Manage the CRUD (Create, Read, Update, Delete) operations for their respective models.
*   **`api_views.py`**: Provides asynchronous endpoints for front-end JavaScript fetch requests.

### 2. Business Logic Layer (Services)
The `finance/services/` directory contains all core business rules:
*   **`base_service.py`**: A base class containing shared methods inherited by other services.
*   **`transaction_service.py`, `wallet_service.py`, `budget_service.py`, `category_service.py`**: Encapsulate data creation and manipulation logic before interacting with the database.
*   **`exchange_service.py`**: Manages the logic for currency conversion rates and calculations.

### 3. External Integration (Clients)
*   **`finance/clients/exchange_client.py`**: Responsible for making HTTP requests to external third-party currency exchange APIs.

### 4. Data Transfer and Mapping (DTOs & Mappers)
*   **`finance/dtos/`**: Contains Data Transfer Object classes (`transaction_dto.py`, `wallet_dto.py`, etc.) that standardize how data is passed between the front-end and the service layer.
*   **`finance/mappers/`**: Utility classes designed to convert Django Model instances into DTOs and vice-versa.

### 5. Front-End (Templates & Static)
*   **`finance/templates/finance/`**: Houses all HTML files, including the base `layout.html`, management views (`manage_transactions.html`), and dynamic UI components inside the `includes/` subfolder (like modals).
*   **`finance/static/finance/`**: 
    *   **`css/`**: Contains `index.css` for custom styling and overrides on top of the Bootstrap framework.
    *   **`js/`**: Contains core scripts (`finance.js`, `shared.js`) responsible for UI interactivity, asynchronous requests, and `Chart.js` graph rendering.

### 6. Custom Commands
*   **`finance/management/commands/`**: Contains `seed_categories.py`, which are used to prepopulate the database with necessary initial categories.

---

## How to Run the Application

Follow these steps to run the project in your local development environment:

1.  **Prerequisites**: Ensure that you have Python 3.10+ and `pip` installed on your machine.
2.  **Install Dependencies**:
    Navigate to the root directory of the project (where `manage.py` is located) and install the required packages:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  **Database Setup**:
    Run Django migrations to create the necessary tables in the default SQLite database:
    ```bash
    python manage.py makemigrations finance
    python manage.py migrate
    ```
4.  **Seed the Database (Optional but Recommended)**:
    Generate the initial data by running the custom management commands:
    ```bash
    python manage.py seed_categories
    ```
5.  **Start the Server**:
    Launch the Django development server:
    ```bash
    python manage.py runserver
    ```
6.  **Access the App**: 
    Open your web browser and navigate to `http://127.0.0.1:8000/`. Register a new account to begin tracking your finances.

---

## Additional Information

*   **Icon Fallbacks:** The file `finance/data/fallback_icons.json` is used to ensure Bootstrap icons load gracefully in the event of network failures or if categories are created without defined icons.
*   **Code Quality:** The project was developed with a strict focus on code formatting and quality, utilizing tools like `djlint` for Django templates, `cssbeautifier` for styling, and standard Python formatters guided by an `.editorconfig` file.
