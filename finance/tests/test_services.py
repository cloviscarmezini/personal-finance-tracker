from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from finance.services.wallet_service import WalletService
from finance.services.transaction_service import TransactionService
from finance.services.category_service import CategoryService
from finance.services.budget_service import BudgetService
from finance.models import Wallet, Category, Transaction, Budget


class MockExchangeService:
    def get_pair_rate(self, from_currency, to_currency):
        return Decimal("2.0000")


class ServicesLayerTestCase(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username="testuser", password="pass")
        self.wallet_service = WalletService()
        self.category_service = CategoryService()
        self.budget_service = BudgetService()
        self.transaction_service = TransactionService(exchange_service=MockExchangeService())

    def test_wallet_create_and_update(self):
        wallet = self.wallet_service.create_wallet(self.user, "savings", "usd", "100.00")
        self.assertEqual(wallet.currency, "USD")
        self.assertEqual(wallet.name, "savings")
        self.assertEqual(wallet.balance, Decimal("100.00"))

        wallet = self.wallet_service.update_wallet(wallet.id, self.user, "updated", "EUR", "150.00")
        self.assertEqual(wallet.currency, "EUR")
        self.assertEqual(wallet.balance, Decimal("150.00"))

    def test_wallet_update_balance_optional(self):
        wallet = self.wallet_service.create_wallet(self.user, "savings", "BRL", "100.00")
        wallet = self.wallet_service.update_wallet(wallet.id, self.user, "savings", "BRL")
        self.assertEqual(wallet.balance, Decimal("100.00"))

    def test_wallet_delete_raises_for_missing(self):
        with self.assertRaises(Wallet.DoesNotExist):
            self.wallet_service.delete_wallet(9999, self.user)

    def test_category_create_update_reset(self):
        category = self.category_service.create_category(self.user, "Bills", "#111111", "bi-wallet")
        self.assertEqual(category.name, "Bills")
        self.assertEqual(category.color, "#111111")

        category = self.category_service.update_category(category.id, self.user, "Bills Updated", "#222222", "bi-wallet")
        self.assertEqual(category.name, "Bills Updated")

        system_default = Category.objects.create(name="Default", color="#333333", icon="bi-tag", is_system_default=True)
        restored = self.category_service.reset_categories(self.user)
        self.assertEqual(len(restored), 1)
        self.assertEqual(restored[0].name, "Default")

    def test_budget_create_and_status(self):
        category = Category.objects.create(user=self.user, name="Food")
        budget = self.budget_service.create_threshold(self.user, category.id, "200.00", 7, 2026)
        self.assertEqual(budget.amount_limit, Decimal("200.00"))
        self.assertEqual(budget.month, 7)
        self.assertEqual(budget.year, 2026)

        budget.amount_limit = Decimal("100.00")
        budget.save()
        report = self.budget_service.get_budget_status(self.user, 2026, 7, exchange_service=self.transaction_service.exchange_service)
        self.assertIsInstance(report, list)

    def test_transaction_create_inflow_and_outflow(self):
        wallet = self.wallet_service.create_wallet(self.user, "Main", "BRL", "100.00")
        category = self.category_service.create_category(self.user, "Bills", "#000000", "bi-tag")

        transaction = self.transaction_service.create(
            user=self.user,
            wallet_id=wallet.id,
            category_id=category.id,
            t_type="inflow",
            amount="100.00",
            description="Paycheck",
            t_date=date(2026, 7, 4),
        )
        self.assertEqual(transaction.transaction_type, "INFLOW")
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, Decimal("200.00"))

        expense = self.transaction_service.create(
            user=self.user,
            wallet_id=wallet.id,
            category_id="",
            t_type="outflow",
            amount="50.00",
            description="Gas",
            t_date=date(2026, 7, 5),
        )
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, Decimal("150.00"))

    def test_transaction_update_and_delete(self):
        wallet = self.wallet_service.create_wallet(self.user, "Main", "BRL", "100.00")
        transaction = self.transaction_service.create(
            user=self.user,
            wallet_id=wallet.id,
            category_id="",
            t_type="outflow",
            amount="40.00",
            description="Dinner",
            t_date=date(2026, 7, 5),
        )
        updated = self.transaction_service.update_transaction(transaction.id, self.user, description="Dinner out")
        self.assertEqual(updated.description, "Dinner out")

        self.transaction_service.delete_transaction(transaction.id, self.user)
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, Decimal("100.00"))

    def test_transaction_create_invalid_type(self):
        wallet = self.wallet_service.create_wallet(self.user, "Main", "BRL", "100.00")
        with self.assertRaises(ValidationError):
            self.transaction_service.create(
                user=self.user,
                wallet_id=wallet.id,
                category_id="",
                t_type="invalid",
                amount="10.00",
                description="",
                t_date=date(2026, 7, 7),
            )

    def test_update_base_currency_validation(self):
        with self.assertRaises(ValidationError):
            self.transaction_service.update_base_currency(self.user, "XYZ")
