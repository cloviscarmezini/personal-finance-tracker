import os
from datetime import date
import requests
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404
from dotenv import load_dotenv
from django.core.cache import cache

from decimal import Decimal

from .models import User, Wallet, Category, Budget, Transaction

load_dotenv()
class ExchangeRateClient:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://v6.exchangerate-api.com/v6"

    def get_pair_rate(self, from_currency: str, to_currency: str) -> Decimal:
        if from_currency == to_currency:
            return Decimal("1.0000")

        cache_key = f"rate_{from_currency}_{to_currency}"
        
        cached_rate = cache.get(cache_key)
        if cached_rate is not None:
            return Decimal(str(cached_rate))

        try:
            url = f"{self.base_url}/{self.api_key}/pair/{from_currency}/{to_currency}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if data.get("result") == "success":
                rate_value = data.get("conversion_rate")
                
                cache.set(cache_key, rate_value, timeout=3600)
                
                return Decimal(str(rate_value))
        except Exception as e:
            print(f"[Exchange Cache Engine] API Failure, applying emergency fallback: {e}")
        
        return Decimal("1.0000")

exchange_client = ExchangeRateClient(api_key=os.getenv("EXCHANGE_RATE_API_KEY"))

def process_recurring_transactions(user) -> None:
    today = date.today()
    pending_recurring = Transaction.objects.filter(
        wallet__user=user, is_recurring=True, next_due_date__lte=today
    )
    if not pending_recurring.exists():
        return
    with db_transaction.atomic():
        for item in pending_recurring:
            Transaction.objects.create(
                wallet=item.wallet, category=item.category, transaction_type=item.transaction_type,
                amount=item.amount, amount_in_base_currency=item.amount_in_base_currency,
                exchange_rate_used=item.exchange_rate_used, description=f"[Recurring] {item.description}",
                date=today, is_recurring=False
            )
            try:
                if item.next_due_date.month == 12:
                    item.next_due_date = item.next_due_date.replace(year=item.next_due_date.year + 1, month=1)
                else:
                    item.next_due_date = item.next_due_date.replace(month=item.next_due_date.month + 1)
            except ValueError:
                item.next_due_date = item.next_due_date.replace(day=28, month=item.next_due_date.month + 1)
            item.save()

def create_user_with_default_categories(username, email, password, base_currency) -> User:
    with db_transaction.atomic():
        user = User.objects.create_user(username, email, password)
        user.base_currency = base_currency
        user.save()
        
        system_defaults = Category.objects.filter(is_system_default=True)
        for sys_cat in system_defaults:
            Category.objects.create(user=user, name=sys_cat.name, color=sys_cat.color, icon=sys_cat.icon, is_system_default=False)
            
        return user

def reset_user_categories(user) -> None:
    with db_transaction.atomic():
        Category.objects.filter(user=user).delete()

        system_defaults = Category.objects.filter(is_system_default=True)
        for sys_cat in system_defaults:
            Category.objects.create(
                user=user, 
                name=sys_cat.name, 
                color=sys_cat.color, 
                icon=sys_cat.icon, 
                is_system_default=False
            )

def execute_financial_transaction(user, wallet_id, category_id, t_type, amount, description, t_date) -> Transaction:
    wallet = get_object_or_404(Wallet, id=wallet_id, user=user)
    category = get_object_or_404(Category, id=category_id, user=user) if category_id else None
    rate = exchange_client.get_pair_rate(wallet.currency, user.base_currency)
    amount_in_base = amount * rate
    with db_transaction.atomic():
        transaction = Transaction.objects.create(
            wallet=wallet, category=category, transaction_type=t_type, amount=amount,
            amount_in_base_currency=amount_in_base, exchange_rate_used=rate,
            description=description, date=t_date
        )
        if t_type == "INFLOW":
            wallet.balance += amount
        else:
            wallet.balance -= amount
        wallet.save()
    return transaction


def create_wallet(user, name, currency) -> Wallet:
    return Wallet.objects.create(user=user, name=name, currency=currency)

def update_wallet(user, wallet_id, name, currency) -> Wallet:
    wallet = get_object_or_404(Wallet, id=wallet_id, user=user)
    wallet.name = name
    wallet.currency = currency
    wallet.save()
    return wallet

def delete_wallet(user, wallet_id) -> None:
    wallet = get_object_or_404(Wallet, id=wallet_id, user=user)
    wallet.delete()

def create_category(user, name, color, icon) -> Category:
    return Category.objects.create(user=user, name=name, color=color, icon=icon)

def update_category(user, category_id, name, color, icon) -> Category:
    category = get_object_or_404(Category, id=category_id, user=user)
    category.name = name
    category.color = color
    category.icon = icon
    category.save()
    return category

def delete_category(user, category_id) -> None:
    category = get_object_or_404(Category, id=category_id, user=user)
    category.delete()

def create_budget(user, category_id, amount_limit, month, year) -> Budget:
    category = get_object_or_404(Category, id=category_id, user=user)
    return Budget.objects.create(user=user, category=category, amount_limit=amount_limit, month=month, year=year)

def update_budget(user, budget_id, amount_limit, month, year) -> Budget:
    budget = get_object_or_404(Budget, id=budget_id, user=user)
    budget.amount_limit = amount_limit
    budget.month = month
    budget.year = year
    budget.save()
    return budget

def delete_budget(user, budget_id) -> None:
    budget = get_object_or_404(Budget, id=budget_id, user=user)
    budget.delete()

@db_transaction.atomic
def update_user_base_currency(user, new_currency: str):
    allowed_currencies = ["USD", "BRL", "EUR", "GBP", "ARS"]
    if new_currency not in allowed_currencies:
        raise ValueError("Target currency is outside supported domain matrices.")
        
    user.base_currency = new_currency
    user.save()
    return user
