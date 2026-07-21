from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.shortcuts import render
from django.http import JsonResponse
from datetime import date
from finance.services import wallet_service, category_service, transaction_service, exchange_service

@login_required
@require_GET
def index(request):
    user = request.user
    return render(request, "finance/index.html", {
        "wallets": wallet_service.list_wallets(user),
        "categories": category_service.list_categories(user),
        "base_currency": user.base_currency,
        "net_worth": float(wallet_service.get_consolidated_net_worth(user, exchange_service)),
    })

@login_required
@require_GET
def get_chart_data(request):
    user = request.user
    today = date.today()
    try:
        target_month = int(request.GET.get("month", today.month))
        target_year = int(request.GET.get("year", today.year))
    except ValueError:
        target_month = today.month
        target_year = today.year
    chart_data = transaction_service.get_category_chart_metrics(user=user, target_year=target_year, target_month=target_month)
    return JsonResponse({
        "status": "success",
        "base_currency": user.base_currency,
        "data": chart_data
    })
