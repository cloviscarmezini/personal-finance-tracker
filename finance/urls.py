from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),

    path("manage/transactions", views.manage_transactions, name="manage_transactions"),
    path("manage/transactions/create", views.create_transaction, name="create_transaction"),
    path("manage/transactions/edit/<int:transaction_id>", views.edit_transaction, name="edit_transaction"),
    path("manage/transactions/delete/<int:transaction_id>", views.delete_transaction, name="delete_transaction"),

    path("manage/wallets", views.manage_wallets, name="manage_wallets"),
    path("manage/wallets/create", views.create_wallet, name="create_wallet"),
    path("manage/wallets/edit/<int:wallet_id>", views.edit_wallet, name="edit_wallet"),
    path("manage/wallets/delete/<int:wallet_id>", views.delete_wallet, name="delete_wallet"),

    path("manage/categories", views.manage_categories, name="manage_categories"),
    path("manage/categories/create", views.create_category, name="create_category"),
    path("manage/categories/edit/<int:category_id>", views.edit_category, name="edit_category"),
    path("manage/categories/delete/<int:category_id>", views.delete_category, name="delete_category"),
    path("manage/categories/reset", views.reset_categories, name="reset_categories"),

    path("manage/budgets", views.manage_budgets, name="manage_budgets"),
    path("manage/budgets/create", views.create_budget, name="create_budget"),
    path("manage/budgets/edit/<int:budget_id>", views.edit_budget, name="edit_budget"),
    path("manage/budgets/delete/<int:budget_id>", views.delete_budget, name="delete_budget"),

    path("user/settings/currency", views.update_base_currency, name="update_base_currency"),

    path("api/resources/transaction/create", api_views.create_transaction, name="api_create_transaction"),
    path("api/resources/wallet/create", api_views.create_wallet, name="api_create_wallet"),
    path("api/resources/category/create", api_views.create_category, name="api_create_category"),
    path("api/resources/budget/create", api_views.create_budget, name="api_create_budget"),
    path("api/resources/currencies/", api_views.get_currencies, name="api_get_currencies"),
    path("api/resources/icons", api_views.get_icons_api, name="get_icons_api"),

    path("api/metrics/balance", api_views.get_balance_metrics, name="api_metrics_balance"),
    path("api/analytics/balance-metrics", api_views.get_balance_metrics, name="api_analytics_balance_metrics"),
    path("api/analytics/chart", api_views.get_chart_data, name="api_analytics_chart"),
    path("api/analytics/budget", api_views.get_budget_status, name="api_analytics_budget"),
]
