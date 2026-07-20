from datetime import date
from django.db.models import Sum, Q
from decimal import Decimal
from .models import Wallet, Transaction, Budget
from .services import exchange_client

def get_consolidated_net_worth(user) -> float:
    wallets = Wallet.objects.filter(user=user)
    total_net_worth = 0.0
    for wallet in wallets:
        rate = exchange_client.get_pair_rate(wallet.currency, user.base_currency)
        total_net_worth += float(wallet.balance) * float(rate)
    return total_net_worth

def get_balance_metrics(user, target_year: int, target_month: int, start_date=None, end_date=None, wallet_id=None, category_id=None, min_amount=None, max_amount=None) -> dict:
    today = date.today()
    base_currency = user.base_currency
    
    criteria_q = Q(wallet__user=user)
    if wallet_id:
        criteria_q &= Q(wallet_id=wallet_id)
    if min_amount:
        criteria_q &= Q(amount__gte=Decimal(min_amount))
    if max_amount:
        criteria_q &= Q(amount__lte=Decimal(max_amount))
    if category_id:
        if category_id == "uncategorized":
            criteria_q &= Q(category__isnull=True)
        else:
            criteria_q &= Q(category_id=category_id)

    if start_date or end_date:
        up_to_date = end_date if end_date else str(today)
        accumulated_metric_type = "current_balance"
        accumulated_q = criteria_q & Q(date__lte=up_to_date)
    else:
        target_deadline = date(target_year, target_month, 28)
        current_deadline = date(today.year, today.month, 28)
        
        if target_deadline < current_deadline:
            accumulated_metric_type = "end_month_balance"
            accumulated_q = criteria_q & Q(date__lt=date(target_year if target_month < 12 else target_year + 1, target_month + 1 if target_month < 12 else 1, 1))
        elif target_deadline > current_deadline:
            accumulated_metric_type = "projected_balance"
            accumulated_q = criteria_q & Q(date__lt=date(target_year if target_month < 12 else target_year + 1, target_month + 1 if target_month < 12 else 1, 1))
        else:
            accumulated_metric_type = "current_balance"
            accumulated_q = criteria_q & Q(date__lte=today)

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

    acc_totals = Transaction.objects.filter(accumulated_q)\
                                    .values('wallet_id', 'wallet__currency', 'transaction_type')\
                                    .annotate(total=Sum('amount'))

    int_totals = Transaction.objects.filter(interval_q)\
                                    .values('wallet_id', 'wallet__currency', 'transaction_type')\
                                    .annotate(total=Sum('amount'))

    accumulated_balance = 0.0
    interval_balance = 0.0

    for entry in acc_totals:
        rate = float(exchange_client.get_pair_rate(entry['wallet__currency'], base_currency))
        factor = 1.0 if entry['transaction_type'] == 'INFLOW' else -1.0
        accumulated_balance += float(entry['total']) * factor * rate

    for entry in int_totals:
        rate = float(exchange_client.get_pair_rate(entry['wallet__currency'], base_currency))
        factor = 1.0 if entry['transaction_type'] == 'INFLOW' else -1.0
        interval_balance += float(entry['total']) * factor * rate

    return {
        "accumulated_metric_type": accumulated_metric_type,
        "accumulated_balance": accumulated_balance,
        "interval_metric_type": interval_metric_type,
        "interval_balance": interval_balance,
        "base_currency": base_currency
    }

def get_monthly_chart_data(user) -> dict:
    today = date.today()
    transactions = Transaction.objects.filter(
        wallet__user=user, transaction_type="OUTFLOW", date__year=today.year, date__month=today.month
    ).values('category__name', 'category__color').annotate(total=Sum('amount_in_base_currency')).order_by('-total')
    labels, datasets_data, colors = [], [], []
    for t in transactions:
        labels.append(t['category__name'] if t['category__name'] else "Uncategorized")
        datasets_data.append(float(t['total']))
        colors.append(t['category__color'] if t['category__color'] else "#adb5bd")
    return {"labels": labels, "datasets_data": datasets_data, "colors": colors}

def get_monthly_budget_status(user) -> list:
    today = date.today()
    budgets = Budget.objects.filter(user=user, month=today.month, year=today.year).select_related('category')
    status_list = []
    for budget in budgets:
        spent_agg = Transaction.objects.filter(
            wallet__user=user, category=budget.category, transaction_type="OUTFLOW", date__month=today.month, date__year=today.year
        ).aggregate(total=Sum('amount_in_base_currency'))
        spent = float(spent_agg['total'] or 0.00)
        limit = float(budget.amount_limit)
        percentage = (spent / limit * 100) if limit > 0 else 0
        status_list.append({"category": budget.category.name if budget.category else "Uncategorized", "limit": limit, "spent": spent, "percentage": round(percentage, 1)})
    return status_list
