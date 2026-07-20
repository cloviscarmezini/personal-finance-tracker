from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    
    path("manage/wallets", views.manage_wallets, name="manage_wallets"),
    path("manage/wallets/edit/<int:wallet_id>", views.edit_wallet, name="edit_wallet"),
    path("manage/wallets/delete/<int:wallet_id>", views.delete_wallet_view, name="delete_wallet"),
    
    path("manage/categories", views.manage_categories, name="manage_categories"),
    path("manage/categories/edit/<int:category_id>", views.edit_category, name="edit_category"),
    path("manage/categories/delete/<int:category_id>", views.delete_category_view, name="delete_category"),
    path("manage/categories/reset", views.reset_categories_view, name="reset_categories"),
    
    path("manage/budgets", views.manage_budgets, name="manage_budgets"),
    path("manage/budgets/edit/<int:budget_id>", views.edit_budget, name="edit_budget"),
    path("manage/budgets/delete/<int:budget_id>", views.delete_budget_view, name="delete_budget"),
    
    path("transaction/create", views.create_transaction, name="create_transaction"),
    path("manage/transactions", views.manage_transactions, name="manage_transactions"),
    path("manage/transactions/edit/<int:transaction_id>", views.edit_transaction, name="edit_transaction"),
    path("manage/transactions/delete/<int:transaction_id>", views.delete_transaction_view, name="delete_transaction"),
    
    path("api/resources/wallet/create", views.api_create_wallet, name="api_create_wallet"),
    path("api/resources/category/create", views.api_create_category, name="api_create_category"),
    path("api/resources/budget/create", views.api_create_budget, name="api_create_budget"),
    
    path("api/analytics/chart", views.get_chart_data, name="get_chart_data"),
    path("api/analytics/budget", views.get_budget_status, name="get_budget_status"),
    path("api/analytics/balance-metrics", views.api_balance_metrics, name="api_balance_metrics"),
]
