from decimal import Decimal
from datetime import date
from django.db import models
from django.db.models import Q, Sum
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class User(AbstractUser):
    base_currency = models.CharField(max_length=3, default="BRL")


class WalletQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user).order_by("-created_at")

    def get_for_user(self, user, wallet_id):
        return self.for_user(user).get(id=wallet_id)

    def select_for_user(self, user, wallet_id):
        return self.for_user(user).select_for_update().get(id=wallet_id)

    def get_consolidated_net_worth(self, base_currency, exchange_service):
        total_net_worth = Decimal("0.00")
        for wallet in self:
            rate = exchange_service.get_pair_rate(wallet.currency, base_currency)
            total_net_worth += wallet.balance * rate
        return total_net_worth


class WalletManager(models.Manager):
    def get_queryset(self):
        return WalletQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)

    def get_for_user(self, user, wallet_id):
        return self.get_queryset().get_for_user(user, wallet_id)

    def select_for_user(self, user, wallet_id):
        return self.get_queryset().select_for_user(user, wallet_id)

    def get_consolidated_net_worth(self, user, base_currency, exchange_service):
        return self.get_queryset().for_user(user).get_consolidated_net_worth(base_currency, exchange_service)


class Wallet(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallets")
    name = models.CharField(max_length=50)
    currency = models.CharField(max_length=3, default="BRL")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    objects = WalletManager()


class CategoryQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user).order_by("name")

    def get_for_user(self, user, category_id):
        return self.for_user(user).get(id=category_id)


class CategoryManager(models.Manager):
    def get_queryset(self):
        return CategoryQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)

    def get_for_user(self, user, category_id):
        return self.get_queryset().get_for_user(user, category_id)


class Category(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories", null=True, blank=True)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#6c757d")
    icon = models.CharField(max_length=50, default="bi-tag")
    is_system_default = models.BooleanField(default=False)

    objects = CategoryManager()

    class Meta:
        verbose_name_plural = "Categories"


class BudgetQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user).select_related("category").order_by("-year", "-month", "category__name")

    def get_for_user(self, user, budget_id):
        return self.for_user(user).get(id=budget_id)

    def active_for_month_year(self, user, month, year):
        return self.for_user(user).filter(month=month, year=year)

    def get_monthly_budget_status(self, user, target_year, target_month, base_currency, exchange_service):
        active_budgets = self.active_for_month_year(user, target_month, target_year)
        actual_outflows = Transaction.objects.for_user(user).filter(
            date__year=target_year,
            date__month=target_month,
            transaction_type="OUTFLOW"
        ).values("category_id", "wallet__currency").annotate(total_spent=Sum("amount"))

        spent_map = {}
        for entry in actual_outflows:
            cat_id = entry.get("category_id")
            if not cat_id:
                continue
            rate = exchange_service.get_pair_rate(entry.get("wallet__currency", base_currency), base_currency)
            converted_spent = Decimal(str(entry.get("total_spent", 0))) * rate
            spent_map[cat_id] = spent_map.get(cat_id, Decimal("0.00")) + converted_spent

        report = []
        for budget in active_budgets:
            limit_in_base = Decimal(str(budget.amount_limit))
            current_spent = spent_map.get(budget.category.id, Decimal("0.00"))
            usage_percentage = round((current_spent / limit_in_base) * 100, 2) if limit_in_base > 0 else Decimal("0.00")
            report.append({
                "budget_id": budget.id,
                "category_id": budget.category.id,
                "category_name": budget.category.name,
                "category_color": budget.category.color,
                "category_icon": budget.category.icon,
                "amount_limit": float(limit_in_base),
                "amount_spent": float(current_spent),
                "usage_percentage": float(usage_percentage),
                "is_over_budget": current_spent > limit_in_base
            })
        return report


class BudgetManager(models.Manager):
    def get_queryset(self):
        return BudgetQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)

    def get_for_user(self, user, budget_id):
        return self.get_queryset().get_for_user(user, budget_id)

    def active_for_month_year(self, user, month, year):
        return self.get_queryset().active_for_month_year(user, month, year)

    def get_monthly_budget_status(self, user, target_year, target_month, base_currency, exchange_service):
        return self.get_queryset().get_monthly_budget_status(user, target_year, target_month, base_currency, exchange_service)


class Budget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="budgets")
    amount_limit = models.DecimalField(max_digits=12, decimal_places=2)
    month = models.IntegerField()
    year = models.IntegerField()

    objects = BudgetManager()


class TransactionQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(wallet__user=user).select_related("wallet", "category")

    def get_for_user(self, user, transaction_id):
        return self.for_user(user).get(id=transaction_id)

    def filter_for_user(
        self,
        user,
        target_year=None,
        target_month=None,
        wallet_id=None,
        category_id=None,
        start_date=None,
        end_date=None,
        min_amount=None,
        max_amount=None,
    ):
        queryset = self.for_user(user)

        if wallet_id:
            queryset = queryset.filter(wallet_id=wallet_id)

        if min_amount is not None and min_amount != "":
            queryset = queryset.filter(amount__gte=Decimal(str(min_amount)))

        if max_amount is not None and max_amount != "":
            queryset = queryset.filter(amount__lte=Decimal(str(max_amount)))

        if category_id:
            if category_id == "uncategorized":
                queryset = queryset.filter(category__isnull=True)
            else:
                queryset = queryset.filter(category_id=category_id)

        if start_date or end_date:
            if start_date:
                queryset = queryset.filter(date__gte=start_date)
            if end_date:
                queryset = queryset.filter(date__lte=end_date)
        elif target_year is not None and target_month is not None:
            queryset = queryset.filter(date__year=target_year, date__month=target_month)

        return queryset

    def balance_aggregates(self, user, base_currency, exchange_service):
        totals = self.for_user(user).values("wallet__currency", "transaction_type").annotate(total=Sum("amount"))
        accumulated_balance = Decimal("0.00")
        for entry in totals:
            rate = exchange_service.get_pair_rate(entry["wallet__currency"], base_currency)
            factor = Decimal("1.00") if entry["transaction_type"] == "INFLOW" else Decimal("-1.00")
            accumulated_balance += Decimal(str(entry["total"])) * factor * rate
        return float(accumulated_balance)

    def get_balance_metrics(
        self,
        user,
        target_year,
        target_month,
        start_date=None,
        end_date=None,
        wallet_id=None,
        category_id=None,
        min_amount=None,
        max_amount=None,
        base_currency="BRL",
        exchange_service=None,
    ):
        base_currency = base_currency.upper()
        criteria_q = Q(wallet__user=user)

        if wallet_id:
            criteria_q &= Q(wallet_id=wallet_id)
        if min_amount:
            criteria_q &= Q(amount__gte=Decimal(str(min_amount)))
        if max_amount:
            criteria_q &= Q(amount__lte=Decimal(str(max_amount)))
        if category_id:
            if category_id == "uncategorized":
                criteria_q &= Q(category__isnull=True)
            else:
                criteria_q &= Q(category_id=category_id)

        if start_date or end_date:
            up_to_date = end_date if end_date else str(date.today())
            accumulated_metric_type = "current_balance"
            accumulated_q = criteria_q & Q(date__lte=up_to_date)
        else:
            target_deadline = date(target_year, target_month, 28)
            current_deadline = date(date.today().year, date.today().month, 28)
            if target_deadline < current_deadline:
                accumulated_metric_type = "end_month_balance"
                accumulated_q = criteria_q & Q(date__lt=date(target_year if target_month < 12 else target_year + 1, target_month + 1 if target_month < 12 else 1, 1))
            elif target_deadline > current_deadline:
                accumulated_metric_type = "projected_balance"
                accumulated_q = criteria_q & Q(date__lt=date(target_year if target_month < 12 else target_year + 1, target_month + 1 if target_month < 12 else 1, 1))
            else:
                accumulated_metric_type = "current_balance"
                accumulated_q = criteria_q & Q(date__lte=date.today())

        if start_date or end_date:
            interval_metric_type = "balance"
            interval_q = criteria_q
            if start_date:
                interval_q &= Q(date__gte=start_date)
            if end_date:
                interval_q &= Q(date__lte=end_date)
        else:
            interval_metric_type = "monthly_balance"
            interval_q = criteria_q & Q(date__year=target_year, date__month=target_month)

        acc_totals = self.filter(accumulated_q).values("wallet__currency", "transaction_type").annotate(total=Sum("amount"))
        int_totals = self.filter(interval_q).values("wallet__currency", "transaction_type").annotate(total=Sum("amount"))

        accumulated_balance = Decimal("0.00")
        interval_balance = Decimal("0.00")

        for entry in acc_totals:
            rate = exchange_service.get_pair_rate(entry["wallet__currency"], base_currency)
            factor = Decimal("1.00") if entry["transaction_type"] == "INFLOW" else Decimal("-1.00")
            accumulated_balance += Decimal(str(entry["total"])) * factor * rate

        for entry in int_totals:
            rate = exchange_service.get_pair_rate(entry["wallet__currency"], base_currency)
            factor = Decimal("1.00") if entry["transaction_type"] == "INFLOW" else Decimal("-1.00")
            interval_balance += Decimal(str(entry["total"])) * factor * rate

        return {
            "accumulated_metric_type": accumulated_metric_type,
            "accumulated_balance": float(accumulated_balance),
            "interval_metric_type": interval_metric_type,
            "interval_balance": float(interval_balance),
            "base_currency": base_currency
        }

    def monthly_outflows_by_category(self, target_year, target_month):
        return self.filter(
            date__year=target_year,
            date__month=target_month,
            transaction_type="OUTFLOW"
        ).values(
            "category_id",
            "category__name",
            "category__color",
            "wallet__currency"
        ).annotate(total=Sum("amount"))

    def get_category_chart_metrics(self, user, target_year, target_month, base_currency, exchange_service):
        base_currency = base_currency.upper()
        category_totals = self.for_user(user).monthly_outflows_by_category(target_year, target_month)

        consolidated = {}
        for entry in category_totals:
            cat_id = entry.get("category_id") or 0
            cat_name = entry.get("category__name") or "Uncategorized"
            cat_color = entry.get("category__color") or "#adb5bd"
            total_amount = Decimal(str(entry.get("total", 0)))
            rate = exchange_service.get_pair_rate(entry.get("wallet__currency", base_currency), base_currency)
            converted_amount = total_amount * rate

            if cat_id in consolidated:
                consolidated[cat_id]["value"] += float(converted_amount)
            else:
                consolidated[cat_id] = {
                    "id": cat_id,
                    "label": cat_name,
                    "color": cat_color,
                    "value": float(converted_amount)
                }
        return list(consolidated.values())


class TransactionManager(models.Manager):
    def get_queryset(self):
        return TransactionQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)

    def get_for_user(self, user, transaction_id):
        return self.get_queryset().get_for_user(user, transaction_id)

    def filter_for_user(self, *args, **kwargs):
        return self.get_queryset().filter_for_user(*args, **kwargs)

    def get_balance_metrics(self, *args, **kwargs):
        return self.get_queryset().get_balance_metrics(*args, **kwargs)

    def get_category_chart_metrics(self, *args, **kwargs):
        return self.get_queryset().get_category_chart_metrics(*args, **kwargs)


class Transaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name="transactions", null=True, blank=True)
    transaction_type = models.CharField(max_length=7, choices=[("INFLOW", "Inflow"), ("OUTFLOW", "Outflow")])
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_in_base_currency = models.DecimalField(max_digits=12, decimal_places=2)
    exchange_rate_used = models.DecimalField(max_digits=10, decimal_places=4)
    description = models.CharField(max_length=200)
    date = models.DateField()
    is_recurring = models.BooleanField(default=False)
    next_due_date = models.DateField(null=True, blank=True)

    objects = TransactionManager()
    