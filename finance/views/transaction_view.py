from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from decimal import Decimal
from datetime import date
from urllib.parse import urlencode
from finance.models import Transaction
from finance.services import transaction_service
from finance import selectors

@login_required
@require_POST
def create_transaction(request):
    wallet_id = request.POST.get("wallet")
    category_id = request.POST.get("category")
    t_type = request.POST.get("transaction_type")
    amount = Decimal(str(request.POST.get("amount", "0.00")).replace(",", "."))
    description = request.POST.get("description", "")
    t_date = request.POST.get("date")

    transaction_service.create(
        user=request.user,
        wallet_id=wallet_id,
        category_id=category_id,
        t_type=t_type,
        amount=amount,
        description=description,
        t_date=t_date
    )
    return redirect("index")

@login_required
def manage_transactions(request):
    user = request.user
    today = date.today()
    try:
        target_month = int(request.GET.get("month", today.month))
        target_year = int(request.GET.get("year", today.year))
    except ValueError:
        target_month = today.month
        target_year = today.year
    prev_month = target_month - 1 if target_month > 1 else 12
    prev_year = target_year if target_month > 1 else target_year - 1
    next_month = target_month + 1 if target_month < 12 else 1
    next_year = target_year if target_month < 12 else target_year + 1

    wallet_filter = request.GET.get("wallet")
    category_filter = request.GET.get("category")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    min_amount = request.GET.get("min_amount")
    max_amount = request.GET.get("max_amount")
    order = request.GET.get("order", "-date")

    has_date_range = bool(start_date or end_date)
    queryset = Transaction.objects.filter(wallet__user=user).select_related("wallet", "category")
    if wallet_filter: queryset = queryset.filter(wallet_id=wallet_filter)
    if min_amount: queryset = queryset.filter(amount__gte=Decimal(min_amount))
    if max_amount: queryset = queryset.filter(amount__lte=Decimal(max_amount))
    if category_filter:
        if category_filter == "uncategorized": queryset = queryset.filter(category__isnull=True)
        else: queryset = queryset.filter(category_id=category_filter)
    if has_date_range:
        if start_date: queryset = queryset.filter(date__gte=start_date)
        if end_date: queryset = queryset.filter(date__lte=end_date)
    else:
        queryset = queryset.filter(date__year=target_year, date__month=target_month)

    if order == "price_high": queryset = queryset.order_by("-amount")
    elif order == "price_low": queryset = queryset.order_by("amount")
    elif order == "date_asc": queryset = queryset.order_by("date", "id")
    else: queryset = queryset.order_by("-date", "-id")

    metrics = selectors.get_balance_metrics(
        user=user, target_year=target_year, target_month=target_month,
        start_date=start_date, end_date=end_date, wallet_id=wallet_filter,
        category_id=category_filter, min_amount=min_amount, max_amount=max_amount
    )
    nav_params = request.GET.copy()
    for key in ["month", "year", "page"]:
        if key in nav_params: del nav_params[key]
    base_query_string = urlencode(nav_params)
    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    
    return render(request, "finance/manage_transactions.html", {
        "page_obj": page_obj, 
        "wallets": user.wallets.all(), 
        "categories": user.categories.all(),
        "current_filters": request.GET.dict(), 
        "metrics": metrics, 
        "has_date_range": has_date_range,
        "base_query_string": f"&{base_query_string}" if base_query_string else "",
        "timeline": {
            "current_month": target_month, "current_year": target_year,
            "prev_month": prev_month, "prev_year": prev_year, "next_month": next_month, "next_year": next_year,
            "formatted": date(target_year, target_month, 1).strftime("%B %Y")
        }
    })

@login_required
def edit_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, wallet__user=request.user)
    if request.method == "POST":
        transaction.description = request.POST.get("description", "")
        transaction.amount = Decimal(str(request.POST.get("amount", "0.00")).replace(",", "."))
        transaction.date = request.POST.get("date")
        transaction.save()
        return redirect("manage_transactions")
    return render(request, "finance/edit_transaction.html", {"transaction": transaction})

@login_required
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, wallet__user=request.user)
    transaction.delete()
    return redirect("manage_transactions")

@login_required
@require_POST
def update_base_currency(request):
    new_currency = request.POST.get("base_currency")
    if new_currency:
        try:
            transaction_service.update_base_currency(request.user, new_currency)
        except ValueError:
            pass
    return redirect(request.META.get('HTTP_REFERER', 'index'))

@login_required
@require_GET
def api_balance_metrics(request):
    today = date.today()
    try:
        target_month = int(request.GET.get("month", today.month))
        target_year = int(request.GET.get("year", today.year))
    except ValueError:
        target_month = today.month
        target_year = today.year
    metrics = selectors.get_balance_metrics(
        user=request.user, target_year=target_year, target_month=target_month,
        start_date=request.GET.get("start_date") or None, end_date=request.GET.get("end_date") or None,
        wallet_id=request.GET.get("wallet") or None, category_id=request.GET.get("category") or None,
        min_amount=request.GET.get("min_amount") or None, max_amount=request.GET.get("max_amount") or None
    )
    return JsonResponse({"status": "success", "metrics": metrics})
