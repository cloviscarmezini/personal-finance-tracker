from datetime import date
from decimal import Decimal
from django.test import TestCase
from finance.models import Wallet, Category, Budget, Transaction
from django.contrib.auth import get_user_model


class DummyExchangeService:
    def get_pair_rate(self, from_currency, to_currency):
        if from_currency == to_currency:
            return Decimal("1.0000")
        return Decimal("2.0000")


class ModelLayerTestCase(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username="user1", password="pass")
        self.other_user = self.User.objects.create_user(username="user2", password="pass")

        self.wallet = Wallet.objects.create(user=self.user, name="Primary", currency="BRL", balance=Decimal("100.00"))
        self.other_wallet = Wallet.objects.create(user=self.other_user, name="Other", currency="USD", balance=Decimal("50.00"))

        self.category = Category.objects.create(user=self.user, name="Food", color="#ff0000", icon="bi-food")
        self.uncategorized_transaction = Transaction.objects.create(
            wallet=self.wallet,
            category=None,
            transaction_type="OUTFLOW",
            amount=Decimal("20.00"),
            amount_in_base_currency=Decimal("20.00"),
            exchange_rate_used=Decimal("1.0000"),
            description="Lunch",
            date=date(2026, 7, 1)
        )
        self.categorized_transaction = Transaction.objects.create(
            wallet=self.wallet,
            category=self.category,
            transaction_type="OUTFLOW",
            amount=Decimal("30.00"),
            amount_in_base_currency=Decimal("30.00"),
            exchange_rate_used=Decimal("1.0000"),
            description="Groceries",
            date=date(2026, 7, 2)
        )
        self.inflow_transaction = Transaction.objects.create(
            wallet=self.wallet,
            category=self.category,
            transaction_type="INFLOW",
            amount=Decimal("100.00"),
            amount_in_base_currency=Decimal("100.00"),
            exchange_rate_used=Decimal("1.0000"),
            description="Salary",
            date=date(2026, 7, 3)
        )
        self.budget = Budget.objects.create(
            user=self.user,
            category=self.category,
            amount_limit=Decimal("100.00"),
            month=7,
            year=2026,
        )

    def test_wallet_for_user_returns_only_owned_wallets(self):
        wallets = list(Wallet.objects.for_user(self.user))
        self.assertEqual(wallets, [self.wallet])
        self.assertNotIn(self.other_wallet, wallets)

    def test_wallet_get_consolidated_net_worth_uses_exchange_service(self):
        total = Wallet.objects.get_consolidated_net_worth(self.user, "USD", DummyExchangeService())
        self.assertEqual(total, Decimal("200.00"))

    def test_category_for_user_queries_only_user_categories(self):
        Category.objects.create(user=self.other_user, name="Bills")
        categories = list(Category.objects.for_user(self.user))
        self.assertEqual(categories, [self.category])

    def test_budget_monthly_budget_status_reports_spending_and_usage(self):
        report = Budget.objects.get_monthly_budget_status(
            user=self.user,
            target_year=2026,
            target_month=7,
            base_currency="BRL",
            exchange_service=DummyExchangeService()
        )
        self.assertEqual(len(report), 1)
        self.assertEqual(report[0]["category_name"], "Food")
        self.assertEqual(report[0]["amount_spent"], 30.0)
        self.assertEqual(report[0]["usage_percentage"], 30.0)
        self.assertFalse(report[0]["is_over_budget"])

    def test_transaction_filter_for_user_can_select_uncategorized(self):
        results = list(Transaction.objects.filter_for_user(
            user=self.user,
            target_year=2026,
            target_month=7,
            category_id="uncategorized"
        ))
        self.assertEqual(results, [self.uncategorized_transaction])

    def test_transaction_get_balance_metrics_returns_expected_values(self):
        metrics = Transaction.objects.get_balance_metrics(
            user=self.user,
            target_year=2026,
            target_month=7,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 31),
            base_currency="BRL",
            exchange_service=DummyExchangeService()
        )
        self.assertEqual(metrics["accumulated_balance"], 50.0)
        self.assertEqual(metrics["interval_balance"], 50.0)
        self.assertEqual(metrics["base_currency"], "BRL")

    def test_transaction_get_category_chart_metrics_groups_outflows(self):
        chart_data = Transaction.objects.get_category_chart_metrics(
            user=self.user,
            target_year=2026,
            target_month=7,
            base_currency="BRL",
            exchange_service=DummyExchangeService()
        )
        labels = {item["label"]: item["value"] for item in chart_data}
        self.assertIn("Food", labels)
        self.assertIn("Uncategorized", labels)
        self.assertEqual(labels["Food"], 30.0)
        self.assertEqual(labels["Uncategorized"], 20.0)
