from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from finance.models import Category, Transaction, Wallet
from finance.services.base_service import BaseService


class TransactionService(BaseService):
    @staticmethod
    def _normalize_transaction_type(t_type):
        if t_type is None or str(t_type).strip() == "":
            raise ValidationError("Transaction type is required.")
        normalized = str(t_type).strip().upper()
        if normalized not in ("INFLOW", "OUTFLOW"):
            raise ValidationError("Transaction type must be either INFLOW or OUTFLOW.")
        return normalized

    def _resolve_category(self, category_id, user):
        if not category_id:
            return None
        category_id_value = self._parse_int(category_id, "category")
        return Category.objects.filter(id=category_id_value, user=user).first()

    def __init__(self, exchange_service):
        self.exchange_service = exchange_service

    def _resolve_wallet(self, user, wallet_id):
        if not wallet_id:
            raise ValueError("Wallet is required.")
        wallet = Wallet.objects.filter(id=wallet_id, user=user).first()
        if not wallet:
            raise ValueError("Invalid wallet selected.")
        return wallet

    @db_transaction.atomic
    def create(self, user, wallet_id, category_id, t_type, amount, description, t_date) -> Transaction:
        wallet_id_value = self._parse_int(wallet_id, "wallet")
        wallet = Wallet.objects.select_for_user(user, wallet_id_value)
        transaction_type = self._normalize_transaction_type(t_type)
        amount_value = self._parse_decimal(amount, "amount")
        if amount_value <= self._parse_decimal("0.00", "amount"):
            raise ValidationError("Amount must be greater than zero.")
        transaction_date = self._parse_date(t_date, "date")
        category = self._resolve_category(category_id, user)

        base_currency = getattr(user, "base_currency", "BRL").upper()
        wallet_currency = wallet.currency.upper()
        rate_val = self.exchange_service.get_pair_rate(wallet_currency, base_currency)
        rate = Decimal(str(rate_val))
        amount_in_base = amount_value * rate

        transaction = Transaction.objects.create(
            wallet=wallet,
            category=category,
            transaction_type=transaction_type,
            amount=amount_value,
            amount_in_base_currency=amount_in_base,
            exchange_rate_used=rate,
            description=str(description or ""),
            date=transaction_date,
        )

        if transaction.transaction_type == "INFLOW":
            wallet.balance += amount_value
        else:
            wallet.balance -= amount_value
        wallet.save()
        return transaction

    @db_transaction.atomic
    def update_transaction(self, transaction_id, user, category_id=None, description=""):
        transaction_id_value = self._parse_int(transaction_id, "transaction_id")
        transaction = Transaction.objects.filter(id=transaction_id_value, wallet__user=user).first()
        if not transaction:
            raise Transaction.DoesNotExist("Transaction not found.")

        category = self._resolve_category(category_id, user)
        transaction.category = category
        transaction.description = str(description or "").strip()
        transaction.save()
        return transaction

    @db_transaction.atomic
    def delete_transaction(self, transaction_id, user):
        transaction_id_value = self._parse_int(transaction_id, "transaction_id")
        transaction = Transaction.objects.filter(id=transaction_id_value, wallet__user=user).select_related("wallet").first()
        if not transaction:
            raise Transaction.DoesNotExist("Transaction not found.")

        wallet = transaction.wallet
        if transaction.transaction_type == "INFLOW":
            wallet.balance -= transaction.amount
        else:
            wallet.balance += transaction.amount
        wallet.save()
        transaction.delete()

    @db_transaction.atomic
    def update_base_currency(self, user, new_currency: str):
        allowed_currencies = ["USD", "BRL", "EUR", "GBP", "ARS"]
        currency_value = str(new_currency or "").strip().upper()
        if currency_value not in allowed_currencies:
            raise ValidationError("Unsupported currency.")
        user.base_currency = currency_value
        user.save()
        return user

    def list_transactions(
        self,
        user,
        target_year,
        target_month,
        wallet_filter=None,
        category_filter=None,
        start_date=None,
        end_date=None,
        min_amount=None,
        max_amount=None,
        order="-date"
    ):
        queryset = Transaction.objects.filter_for_user(
            user=user,
            target_year=target_year,
            target_month=target_month,
            wallet_id=wallet_filter,
            category_id=category_filter,
            start_date=start_date,
            end_date=end_date,
            min_amount=min_amount,
            max_amount=max_amount,
        )

        if order == "price_high":
            queryset = queryset.order_by("-amount")
        elif order == "price_low":
            queryset = queryset.order_by("amount")
        elif order == "date_asc":
            queryset = queryset.order_by("date", "id")
        else:
            queryset = queryset.order_by("-date", "-id")

        return queryset

    def get_transaction(self, user, transaction_id):
        return Transaction.objects.get_for_user(user, transaction_id)

    def get_balance_metrics(
        self,
        user,
        target_year=None,
        target_month=None,
        start_date=None,
        end_date=None,
        wallet_id=None,
        category_id=None,
        min_amount=None,
        max_amount=None,
    ):
        year_value = self._parse_int(target_year, "year", default=None, minimum=1) if target_year not in (None, "") else None
        month_value = self._parse_int(target_month, "month", default=None, minimum=1, maximum=12) if target_month not in (None, "") else None

        if year_value is None or month_value is None:
            current = date.today()
            year_value = year_value or current.year
            month_value = month_value or current.month

        start_date_value = self._parse_date(start_date, "start_date") if start_date not in (None, "") else None
        end_date_value = self._parse_date(end_date, "end_date") if end_date not in (None, "") else None
        min_amount_value = self._parse_decimal_optional(min_amount, "min_amount")
        max_amount_value = self._parse_decimal_optional(max_amount, "max_amount")

        base_currency = getattr(user, "base_currency", "BRL").upper()
        return Transaction.objects.get_balance_metrics(
            user=user,
            target_year=year_value,
            target_month=month_value,
            start_date=start_date_value,
            end_date=end_date_value,
            wallet_id=wallet_id,
            category_id=category_id,
            min_amount=min_amount_value,
            max_amount=max_amount_value,
            base_currency=base_currency,
            exchange_service=self.exchange_service,
        )

    def get_category_chart_metrics(self, user, target_year=None, target_month=None):
        year_value = self._parse_int(target_year, "year", default=date.today().year, minimum=1)
        month_value = self._parse_int(target_month, "month", default=date.today().month, minimum=1, maximum=12)
        base_currency = getattr(user, "base_currency", "BRL").upper()
        return Transaction.objects.get_category_chart_metrics(
            user=user,
            target_year=year_value,
            target_month=month_value,
            base_currency=base_currency,
            exchange_service=self.exchange_service,
        )
    