from django.test import TestCase
from datetime import date
from decimal import Decimal
from finance.models import Wallet, Category, Transaction, Budget
from finance.mappers.wallet_mapper import WalletMapper
from finance.mappers.category_mapper import CategoryMapper
from finance.mappers.budget_mapper import BudgetMapper
from finance.mappers.transaction_mapper import TransactionMapper
from django.contrib.auth import get_user_model


class MapperLayerTestCase(TestCase):
    def setUp(self):
        self.User = get_user_model()
        user = self.User.objects.create_user(username="mapperuser", password="pass")

        self.wallet = Wallet.objects.create(user=user, name="Wallet1", currency="USD", balance=Decimal("10.00"))
        self.category = Category.objects.create(user=user, name="Travel", color="#123456", icon="bi-plane")
        self.budget = Budget.objects.create(user=user, category=self.category, amount_limit=Decimal("300.00"), month=7, year=2026)
        self.transaction = Transaction.objects.create(
            wallet=self.wallet,
            category=self.category,
            transaction_type="OUTFLOW",
            amount=Decimal("25.00"),
            amount_in_base_currency=Decimal("25.00"),
            exchange_rate_used=Decimal("1.0000"),
            description="Taxi",
            date=date(2026, 7, 10)
        )

    def test_wallet_mapper_response(self):
        dto = WalletMapper.to_response_dto(self.wallet)
        self.assertEqual(dto.id, self.wallet.id)
        self.assertEqual(dto.name, "Wallet1")
        self.assertTrue(dto.edit_url.endswith(str(self.wallet.id)))

    def test_category_mapper_response(self):
        dto = CategoryMapper.to_response_dto(self.category)
        self.assertEqual(dto.name, "Travel")
        self.assertEqual(dto.color, "#123456")

    def test_budget_mapper_response(self):
        dto = BudgetMapper.to_response_dto(self.budget)
        self.assertEqual(dto.category_name, "Travel")
        self.assertEqual(dto.amount_limit, 300.0)

    def test_transaction_mapper_response_uncategorized(self):
        transaction = Transaction.objects.create(
            wallet=self.wallet,
            category=None,
            transaction_type="INFLOW",
            amount=Decimal("50.00"),
            amount_in_base_currency=Decimal("50.00"),
            exchange_rate_used=Decimal("1.0000"),
            description="Gift",
            date=date(2026, 7, 11)
        )
        dto = TransactionMapper.to_response_dto(transaction)
        self.assertEqual(dto.category_name, "Uncategorized")
        self.assertEqual(dto.category_color, "#adb5bd")
        self.assertEqual(dto.category_icon, "bi-question-circle")
