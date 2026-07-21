from .exchange_service import ExchangeRateService
from .transaction_service import TransactionService
from .budget_service import BudgetService
from .wallet_service import WalletService
from .category_service import CategoryService

exchange_service = ExchangeRateService()
transaction_service = TransactionService(exchange_service=exchange_service)
budget_service = BudgetService()
wallet_service = WalletService()
category_service = CategoryService()

__all__ = [
    "ExchangeRateService",
    "TransactionService",
    "BudgetService",
    "WalletService",
    "CategoryService",
    "exchange_service",
    "transaction_service",
    "budget_service",
    "wallet_service",
    "category_service"
]
