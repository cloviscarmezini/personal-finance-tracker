from django.db import transaction as db_transaction
from finance.models import Category, Budget
from decimal import Decimal

class BudgetService:
    @db_transaction.atomic
    def create_threshold(self, user, category_id: int, amount_limit, month: int, year: int) -> Budget:
        category = Category.objects.get(id=category_id, user=user)
        budget = Budget.objects.create(
            user=user,
            category=category,
            amount_limit=Decimal(str(amount_limit)),
            month=month,
            year=year
        )
        return budget
    