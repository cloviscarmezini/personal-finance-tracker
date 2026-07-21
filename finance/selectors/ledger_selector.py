from datetime import date
from django.db.models import Sum, Q
from decimal import Decimal
from finance.models import Transaction
from finance.services import exchange_service

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

    acc_totals = Transaction.objects.filter(accumulated_q).values('wallet__currency', 'transaction_type').annotate(total=Sum('amount'))
    int_totals = Transaction.objects.filter(interval_q).values('wallet__currency', 'transaction_type').annotate(total=Sum('amount'))

    accumulated_balance = Decimal("0.00")
    interval_balance = Decimal("0.00")

    for entry in acc_totals:
        rate = exchange_service.get_pair_rate(entry['wallet__currency'], base_currency)
        factor = Decimal("1.00") if entry['transaction_type'] == 'INFLOW' else Decimal("-1.00")
        accumulated_balance += entry['total'] * factor * rate

    for entry in int_totals:
        rate = exchange_service.get_pair_rate(entry['wallet__currency'], base_currency)
        factor = Decimal("1.00") if entry['transaction_type'] == 'INFLOW' else Decimal("-1.00")
        interval_balance += entry['total'] * factor * rate

    return {
        "accumulated_metric_type": accumulated_metric_type,
        "accumulated_balance": float(accumulated_balance),
        "interval_metric_type": interval_metric_type,
        "interval_balance": float(interval_balance),
        "base_currency": base_currency
    }
