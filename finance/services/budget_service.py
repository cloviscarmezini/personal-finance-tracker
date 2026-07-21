from decimal import Decimal
from datetime import date
from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from finance.models import Category, Budget
from finance.services.base_service import BaseService


class BudgetService(BaseService):

    @db_transaction.atomic
    def create_threshold(self, user, category_id: int, amount_limit, month: int, year: int) -> Budget:
        category = Category.objects.get_for_user(user, category_id)
        amount_limit_value = self._parse_decimal(amount_limit, "amount_limit")
        if amount_limit_value < Decimal("0.00"):
            raise ValidationError("Amount limit must be non-negative.")
        month_value = self._parse_int(month, "month", default=date.today().month, minimum=1, maximum=12)
        year_value = self._parse_int(year, "year", default=date.today().year, minimum=1)

        budget = Budget.objects.create(
            user=user,
            category=category,
            amount_limit=amount_limit_value,
            month=month_value,
            year=year_value,
        )
        return budget

    @db_transaction.atomic
    def update_threshold(self, budget_id, user, amount_limit, month, year):
        budget = Budget.objects.get_for_user(user, budget_id)
        amount_limit_value = self._parse_decimal(amount_limit, "amount_limit")
        if amount_limit_value < Decimal("0.00"):
            raise ValidationError("Amount limit must be non-negative.")
        budget.amount_limit = amount_limit_value
        budget.month = self._parse_int(month, "month", default=budget.month, minimum=1, maximum=12)
        budget.year = self._parse_int(year, "year", default=budget.year, minimum=1)
        budget.save()
        return budget

    @db_transaction.atomic
    def delete_threshold(self, budget_id, user):
        budget = Budget.objects.get_for_user(user, budget_id)
        budget.delete()
        return None

    def list_budgets(self, user):
        return Budget.objects.for_user(user)

    def get_budget(self, user, budget_id):
        return Budget.objects.get_for_user(user, budget_id)

    def get_budget_status(self, user, target_year=None, target_month=None, exchange_service=None):
        year_value = self._parse_int(target_year, "year", default=date.today().year, minimum=1)
        month_value = self._parse_int(target_month, "month", default=date.today().month, minimum=1, maximum=12)
        base_currency = getattr(user, "base_currency", "BRL").upper()
        return Budget.objects.get_monthly_budget_status(
            user=user,
            target_year=year_value,
            target_month=month_value,
            base_currency=base_currency,
            exchange_service=exchange_service,
        )
    