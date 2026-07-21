from django.db.models import Sum
from decimal import Decimal
from finance.models import Transaction, Budget
from finance.services import exchange_service

def _to_decimal(value, default=Decimal("0.00")) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return default


def get_category_chart_metrics(user, target_year: int, target_month: int) -> list:
    base_currency = getattr(user, "base_currency", "BRL").upper()
    category_totals = Transaction.objects.filter(
        wallet__user=user, date__year=target_year, date__month=target_month, transaction_type="OUTFLOW"
    ).values('category_id', 'category__name', 'category__color', 'wallet__currency').annotate(total=Sum('amount'))
    
    consolidated = {}
    for entry in category_totals:
        cat_id = entry.get('category_id') or 0
        cat_name = entry.get('category__name') or "Uncategorized"
        cat_color = entry.get('category__color') or "#adb5bd"
        total_amount = _to_decimal(entry.get('total', 0))
        rate = exchange_service.get_pair_rate(entry.get('wallet__currency', base_currency), base_currency)
        converted_amount = total_amount * rate
        
        if cat_id in consolidated:
            consolidated[cat_id]['value'] += float(converted_amount)
        else:
            consolidated[cat_id] = {
                "id": cat_id,
                "label": cat_name,
                "color": cat_color,
                "value": float(converted_amount)
            }
    return list(consolidated.values())


def get_monthly_budget_status(user, target_year: int, target_month: int) -> list:
    base_currency = getattr(user, "base_currency", "BRL").upper()
    active_budgets = Budget.objects.filter(user=user, month=target_month, year=target_year).select_related('category')
    actual_outflows = Transaction.objects.filter(
        wallet__user=user, date__year=target_year, date__month=target_month, transaction_type="OUTFLOW"
    ).values('category_id', 'wallet__currency').annotate(total_spent=Sum('amount'))
    
    spent_map = {}
    for entry in actual_outflows:
        cat_id = entry.get('category_id')
        if not cat_id:
            continue
        rate = exchange_service.get_pair_rate(entry.get('wallet__currency', base_currency), base_currency)
        converted_spent = _to_decimal(entry.get('total_spent', 0)) * rate
        spent_map[cat_id] = spent_map.get(cat_id, Decimal("0.00")) + converted_spent
        
    report = []
    for budget in active_budgets:
        limit_in_base = _to_decimal(budget.amount_limit)
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
