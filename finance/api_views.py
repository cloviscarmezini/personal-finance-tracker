import json
from datetime import date
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from finance.models import Category, Wallet
from finance.services import budget_service, transaction_service, wallet_service, category_service
from finance.mappers.wallet_mapper import WalletMapper
from finance.mappers.category_mapper import CategoryMapper
from finance.mappers.budget_mapper import BudgetMapper
from finance.mappers.transaction_mapper import TransactionMapper


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
    try:
        wallet = wallet_service.create_wallet(
            user=request.user,
            name=payload.get("name"),
            currency=payload.get("currency", "BRL"),
            balance=payload.get("balance", "0.00"),
        )
    except (ValidationError, ValueError) as exc:
        return _json_error(str(exc), status=400)

    wallet_dto = WalletMapper.to_response_dto(wallet)
    return JsonResponse({"status": "success", "wallet": wallet_dto.to_dict()})


@login_required
@require_POST
def create_category(request):
    payload = _parse_payload(request)
    try:
        category = category_service.create_category(
            user=request.user,
            name=payload.get("name"),
            color=payload.get("color", "#6c757d"),
            icon=payload.get("icon", "bi-tag"),
        )
    except (ValidationError, ValueError) as exc:
        return _json_error(str(exc), status=400)

    category_dto = CategoryMapper.to_response_dto(category)
    return JsonResponse({"status": "success", "category": category_dto.to_dict()})


@login_required
@require_POST
def create_budget(request):
    payload = _parse_payload(request)
    try:
        budget = budget_service.create_threshold(
            user=request.user,
            category_id=payload.get("category") or payload.get("category_id"),
            amount_limit=payload.get("amount_limit", "0.00"),
            month=payload.get("month"),
            year=payload.get("year"),
        )
    except (ValidationError, ValueError) as exc:
        return _json_error(str(exc), status=400)
    except Category.DoesNotExist:
        return _json_error("Category not found.", status=400)

    budget_dto = BudgetMapper.to_response_dto(budget)
    return JsonResponse({"status": "success", "budget": budget_dto.to_dict()})


@login_required
@require_POST
def create_transaction(request):
    payload = _parse_payload(request)
    try:
        transaction = transaction_service.create(
            user=request.user,
            wallet_id=payload.get("wallet"),
            category_id=payload.get("category"),
            t_type=payload.get("transaction_type"),
            amount=payload.get("amount", "0.00"),
            description=payload.get("description", ""),
            t_date=payload.get("date"),
        )
    except (ValidationError, ValueError) as exc:
        return _json_error(str(exc), status=400)
    except (Wallet.DoesNotExist, Category.DoesNotExist):
        return _json_error("Wallet or category not found.", status=400)

    transaction_dto = TransactionMapper.to_response_dto(transaction)
    return JsonResponse({"status": "success", "transaction": transaction_dto.to_dict()})


@login_required
@require_GET
def get_balance_metrics(request):
    try:
        metrics = transaction_service.get_balance_metrics(
            user=request.user,
            target_year=request.GET.get("year"),
            target_month=request.GET.get("month"),
            start_date=request.GET.get("start_date") or None,
            end_date=request.GET.get("end_date") or None,
            wallet_id=request.GET.get("wallet") or None,
            category_id=request.GET.get("category") or None,
            min_amount=request.GET.get("min_amount") or None,
            max_amount=request.GET.get("max_amount") or None,
        )
    except (ValidationError, ValueError) as exc:
        return _json_error(str(exc), status=400)
    return JsonResponse({"status": "success", "metrics": metrics})


@login_required
@require_GET
def get_chart_data(request):
    try:
        chart_data = transaction_service.get_category_chart_metrics(
            user=request.user,
            target_year=request.GET.get("year"),
            target_month=request.GET.get("month"),
        )
    except (ValidationError, ValueError) as exc:
        return _json_error(str(exc), status=400)
    return JsonResponse({"status": "success", "base_currency": request.user.base_currency, "data": chart_data})


@login_required
@require_GET
def get_budget_status(request):
    try:
        budget_status_report = budget_service.get_budget_status(
            user=request.user,
            target_year=request.GET.get("year"),
            target_month=request.GET.get("month"),
            exchange_service=transaction_service.exchange_service,
        )
    except (ValidationError, ValueError) as exc:
        return _json_error(str(exc), status=400)
    return JsonResponse({"status": "success", "base_currency": request.user.base_currency, "budgets": budget_status_report})
