from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from finance.models import Budget, Category
from finance.services import budget_service, category_service, exchange_service


@login_required
def manage_budgets(request):
    if request.method == "POST":
        try:
            budget_service.create_threshold(
                user=request.user,
                category_id=request.POST.get("category") or request.POST.get("category_id"),
                amount_limit=request.POST.get("amount_limit", "0.00"),
                month=request.POST.get("month"),
                year=request.POST.get("year"),
            )
        except Category.DoesNotExist:
            raise Http404("Category not found")
        except (ValidationError, ValueError):
            return redirect(request.META.get("HTTP_REFERER", "manage_budgets"))
        return redirect("manage_budgets")

    budgets = budget_service.list_budgets(request.user)
    paginator = Paginator(budgets, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "finance/manage_budgets.html", {
        "page_obj": page_obj,
        "categories": category_service.list_categories(request.user)
    })

@login_required
@require_POST
def create_budget(request):
    return manage_budgets(request)

@login_required
def edit_budget(request, budget_id):
    try:
        budget = budget_service.get_budget(request.user, budget_id)
    except Budget.DoesNotExist:
        raise Http404("Budget not found")

    if request.method == "POST":
        try:
            budget_service.update_threshold(
                budget_id=budget_id,
                user=request.user,
                amount_limit=request.POST.get("amount_limit"),
                month=request.POST.get("month"),
                year=request.POST.get("year"),
            )
        except (ValidationError, ValueError):
            return redirect(request.META.get("HTTP_REFERER", "manage_budgets"))
        return redirect("manage_budgets")
    return render(request, "finance/edit_budget.html", {"budget": budget})

@login_required
def delete_budget(request, budget_id):
    try:
        budget_service.get_budget(request.user, budget_id)
    except Budget.DoesNotExist:
        raise Http404("Budget not found")
    budget_service.delete_threshold(budget_id=budget_id, user=request.user)
    return redirect("manage_budgets")

@login_required
@require_GET
def get_budget_status(request):
    user = request.user
    today = date.today()
    try:
        target_month = int(request.GET.get("month", today.month))
        target_year = int(request.GET.get("year", today.year))
    except ValueError:
        target_month = today.month
        target_year = today.year

    budget_status_report = budget_service.get_budget_status(
        user=user,
        target_year=target_year,
        target_month=target_month,
        exchange_service=exchange_service
    )
    return JsonResponse({
        "status": "success",
        "base_currency": getattr(user, "base_currency", "BRL"),
        "budgets": budget_status_report
    })
