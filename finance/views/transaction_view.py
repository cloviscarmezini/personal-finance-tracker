from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from datetime import date
from urllib.parse import urlencode
from finance.models import Wallet, Category, Transaction
from finance.services import transaction_service, wallet_service, category_service


@login_required
@require_POST
def create_transaction(request):
    try:
        transaction_service.create(
            user=request.user,
            wallet_id=request.POST.get("wallet"),
            category_id=request.POST.get("category"),
            t_type=request.POST.get("transaction_type"),
            amount=request.POST.get("amount", "0.00"),
            description=request.POST.get("description", ""),
            t_date=request.POST.get("date"),
        )
    except (Wallet.DoesNotExist, Category.DoesNotExist):
        raise Http404("Wallet or category not found")
    except (ValidationError, ValueError):
        return redirect(request.META.get("HTTP_REFERER", "manage_transactions"))
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
    queryset = transaction_service.list_transactions(
        user=user,
        target_year=target_year,
        target_month=target_month,
        wallet_filter=wallet_filter,
        category_filter=category_filter,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        order=order
    )

    metrics = transaction_service.get_balance_metrics(
        user=user,
        target_year=target_year,
        target_month=target_month,
        start_date=start_date or None,
        end_date=end_date or None,
        wallet_id=wallet_filter or None,
        category_id=category_filter or None,
        min_amount=min_amount or None,
        max_amount=max_amount or None
    )
    nav_params = request.GET.copy()
    for key in ["month", "year", "page"]:
        if key in nav_params:
            del nav_params[key]
    base_query_string = urlencode(nav_params)
    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "finance/manage_transactions.html", {
        "page_obj": page_obj,
        "wallets": wallet_service.list_wallets(request.user),
        "categories": category_service.list_categories(request.user),
        "current_filters": request.GET.dict(),
        "metrics": metrics,
        "has_date_range": has_date_range,
        "base_query_string": f"&{base_query_string}" if base_query_string else "",
        "timeline": {
            "current_month": target_month,
            "current_year": target_year,
            "prev_month": prev_month,
            "prev_year": prev_year,
            "next_month": next_month,
            "next_year": next_year,
            "formatted": date(target_year, target_month, 1).strftime("%B %Y")
        }
    })

@login_required
def edit_transaction(request, transaction_id):
    try:
        transaction = transaction_service.get_transaction(request.user, transaction_id)
    except Transaction.DoesNotExist:
        raise Http404("Transaction not found")

    if request.method == "POST":
        try:
            transaction_service.update_transaction(
                transaction_id=transaction_id,
                user=request.user,
                category_id=request.POST.get("category"),
                description=request.POST.get("description", ""),
            )
        except (ValidationError, ValueError):
            return redirect(request.META.get("HTTP_REFERER", "manage_transactions"))
        return redirect("manage_transactions")
    return render(request, "finance/edit_transaction.html", {
        "transaction": transaction,
        "categories": category_service.list_categories(request.user),
    })

@login_required
def delete_transaction(request, transaction_id):
    try:
        transaction_service.get_transaction(request.user, transaction_id)
    except Transaction.DoesNotExist:
        raise Http404("Transaction not found")
    transaction_service.delete_transaction(transaction_id=transaction_id, user=request.user)
    return redirect("manage_transactions")

@login_required
@require_POST
def update_base_currency(request):
    new_currency = request.POST.get("base_currency")
    if new_currency:
        try:
            transaction_service.update_base_currency(request.user, new_currency)
        except (ValidationError, ValueError):
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
    metrics = transaction_service.get_balance_metrics(
        user=request.user,
        target_year=target_year,
        target_month=target_month,
        start_date=request.GET.get("start_date") or None,
        end_date=request.GET.get("end_date") or None,
        wallet_id=request.GET.get("wallet") or None,
        category_id=request.GET.get("category") or None,
        min_amount=request.GET.get("min_amount") or None,
        max_amount=request.GET.get("max_amount") or None
    )
    return JsonResponse({"status": "success", "metrics": metrics})
