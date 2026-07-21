import json
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from finance.models import Wallet, Category, Budget
from finance.services import budget_service, transaction_service
from finance.mappers.transaction_mapper import TransactionMapper
from finance import selectors


def _parse_payload(request):
    content_type = request.content_type or ""
    if content_type.startswith("application/json"):
        try:
            return json.loads(request.body)
        except Exception:
            return {}
    return request.POST


def _json_error(message, status=400):
    return JsonResponse({"status": "error", "message": message}, status=status)


@login_required
@require_POST
def create_wallet(request):
    payload = _parse_payload(request)
    name = payload.get("name", "").strip()
    currency = payload.get("currency", "BRL").strip().upper()
    initial_balance = str(payload.get("balance", "0.00")).replace(",", ".")

    if not name:
        return _json_error("Name is required.", status=400)

    wallet = Wallet.objects.create(
        user=request.user,
        name=name,
        currency=currency,
        balance=Decimal(initial_balance)
    )

    return JsonResponse({
        "status": "success",
        "wallet": {
            "id": wallet.id,
            "name": wallet.name,
            "currency": wallet.currency,
            "balance": float(wallet.balance)
        }
    })


@login_required
@require_POST
def create_category(request):
    payload = _parse_payload(request)
    name = payload.get("name", "").strip()
    color = payload.get("color", "#6c757d").strip()
    icon = payload.get("icon", "bi-tag").strip()

    if not name:
        return _json_error("Name is required.", status=400)

    category = Category.objects.create(user=request.user, name=name, color=color, icon=icon)
    return JsonResponse({
        "status": "success",
        "category": {
            "id": category.id,
            "name": category.name,
            "color": category.color,
            "icon": category.icon
        }
    })


@login_required
@require_POST
def create_budget(request):
    payload = _parse_payload(request)
    category_id = payload.get("category") or payload.get("category_id")
    amount_limit = str(payload.get("amount_limit", "0.00")).replace(",", ".")
    month_value = payload.get("month")
    year_value = payload.get("year")

    if not category_id:
        return _json_error("Category is required.", status=400)

    from datetime import date

    try:
        month = int(month_value) if month_value else None
    except (ValueError, TypeError):
        month = None
    try:
        year = int(year_value) if year_value else None
    except (ValueError, TypeError):
        year = None

    current = date.today()
    month = month or current.month
    year = year or current.year

    budget = budget_service.create_threshold(
        user=request.user,
        category_id=int(category_id),
        amount_limit=float(amount_limit),
        month=month,
        year=year
    )

    return JsonResponse({
        "status": "success",
        "budget": {
            "id": budget.id,
            "category_id": budget.category.id,
            "amount_limit": float(budget.amount_limit),
            "month": budget.month,
            "year": budget.year
        }
    })


@login_required
@require_POST
def create_transaction(request):
    payload = _parse_payload(request)
    wallet_id = payload.get("wallet")
    category_id = payload.get("category")
    t_type = payload.get("transaction_type")
    amount = Decimal(str(payload.get("amount", "0.00")).replace(",", "."))
    description = payload.get("description", "")
    t_date = payload.get("date")

    if not wallet_id or not t_type or not t_date:
        return _json_error("Missing required transaction data.", status=400)

    transaction = transaction_service.create(
        user=request.user,
        wallet_id=wallet_id,
        category_id=category_id,
        t_type=t_type,
        amount=amount,
        description=description,
        t_date=t_date
    )

    transaction_dto = TransactionMapper.to_response_dto(transaction)
    return JsonResponse({"status": "success", "transaction": transaction_dto.to_dict()})


@login_required
@require_GET
def get_balance_metrics(request):
    today = request.GET.get("today")
    try:
        target_month = int(request.GET.get("month", ""))
    except ValueError:
        target_month = None
    try:
        target_year = int(request.GET.get("year", ""))
    except ValueError:
        target_year = None

    if not target_month or not target_year:
        from datetime import date
        current = date.today()
        target_month = target_month or current.month
        target_year = target_year or current.year

    metrics = selectors.get_balance_metrics(
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


@login_required
@require_GET
def get_chart_data(request):
    from datetime import date
    try:
        target_month = int(request.GET.get("month", ""))
    except ValueError:
        target_month = None
    try:
        target_year = int(request.GET.get("year", ""))
    except ValueError:
        target_year = None

    if not target_month or not target_year:
        current = date.today()
        target_month = target_month or current.month
        target_year = target_year or current.year

    chart_data = selectors.get_category_chart_metrics(
        user=request.user,
        target_year=target_year,
        target_month=target_month
    )
    return JsonResponse({"status": "success", "base_currency": request.user.base_currency, "data": chart_data})


@login_required
@require_GET
def get_budget_status(request):
    from datetime import date
    try:
        target_month = int(request.GET.get("month", ""))
    except ValueError:
        target_month = None
    try:
        target_year = int(request.GET.get("year", ""))
    except ValueError:
        target_year = None

    if not target_month or not target_year:
        current = date.today()
        target_month = target_month or current.month
        target_year = target_year or current.year

    budget_status_report = selectors.get_monthly_budget_status(
        user=request.user,
        target_year=target_year,
        target_month=target_month
    )
    return JsonResponse({"status": "success", "base_currency": request.user.base_currency, "budgets": budget_status_report})
