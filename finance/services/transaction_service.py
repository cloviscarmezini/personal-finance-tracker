from decimal import Decimal
from django.db import transaction as db_transaction
from finance.models import Wallet, Category, Transaction

class TransactionService:
    def __init__(self, exchange_service):
        self.exchange_service = exchange_service

    @db_transaction.atomic
    def create(self, user, wallet_id: int, category_id: str, t_type: str, amount: Decimal, description: str, t_date: str) -> Transaction:
        wallet = Wallet.objects.select_for_update().get(id=wallet_id, user=user)
        category = None
        if category_id and str(category_id) != "uncategorized":
            category = Category.objects.get(id=category_id, user=user)
        
        base_currency = getattr(user, "base_currency", "BRL").upper()
        wallet_currency = wallet.currency.upper()
        
        rate_val = self.exchange_service.get_pair_rate(wallet_currency, base_currency)
        rate = Decimal(str(rate_val))
        amt = Decimal(str(amount))
        amount_in_base = amt * rate

        transaction = Transaction.objects.create(
            wallet=wallet,
            category=category,
            transaction_type=t_type.upper(),
            amount=amt,
            amount_in_base_currency=amount_in_base,
            exchange_rate_used=rate,
            description=description,
            date=t_date
        )
        
        if transaction.transaction_type == "INFLOW":
            wallet.balance += amt
        else:
            wallet.balance -= amt
        wallet.save()
        return transaction

    @db_transaction.atomic
    def update_base_currency(self, user, new_currency: str):
        allowed_currencies = ["USD", "BRL", "EUR", "GBP", "ARS"]
        if new_currency not in allowed_currencies:
            raise ValueError("Unsupported currency.")
        user.base_currency = new_currency
        user.save()
        return user
    