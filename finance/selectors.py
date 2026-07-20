from datetime import date
from django.db.models import Sum
from .models import Wallet, Transaction, Budget
from .services import exchange_client

def get_consolidated_net_worth(user) -> float:
    wallets = Wallet.objects.filter(user=user)
    total_net_worth = 0.0

    for wallet in wallets:
        rate = exchange_client.get_pair_rate(wallet.currency, user.base_currency)
        total_net_worth += float(wallet.balance) * float(rate)

    return total_net_worth

def get_monthly_chart_data(user) -> dict:
    today = date.today()
    
    transactions = Transaction.objects.filter(
        wallet__user=user,
        transaction_type="OUTFLOW",
        date__year=today.year,
        date__month=today.month
    ).values('category__name', 'category__color').annotate(total=Sum('amount_in_base_currency')).order_by('-total')

    labels = []
    datasets_data = []
    colors = []

    for t in transactions:
        cat_name = t['category__name'] if t['category__name'] else "Uncategorized"

        labels.append(cat_name)
        datasets_data.append(float(t['total']))
        colors.append(cat_color)

    return {
        "labels": labels,
        "datasets_data": datasets_data,
        "colors": colors
    }

def get_monthly_budget_status(user) -> list:
    today = date.today()
    budgets = Budget.objects.filter(
        user=user, month=today.month, year=today.year
    ).select_related('category')
    
    status_list = []
    for budget in budgets:
        spent_agg = Transaction.objects.filter(
            wallet__user=user,
            category=budget.category,
            transaction_type="OUTFLOW",
            date__month=today.month,
            date__year=today.year
        ).aggregate(total=Sum('amount_in_base_currency'))
        
        spent = float(spent_agg['total'] or 0.00)
        limit = float(budget.amount_limit)
        percentage = (spent / limit * 100) if limit > 0 else 0

        status_list.append({
            "category": budget.category.name,
            "limit": limit,
            "spent": spent,
            "percentage": round(percentage, 1)
        })

    return status_list
