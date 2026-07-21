from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from decimal import Decimal
from datetime import date
from finance.models import Budget
from finance.services import budget_service
from finance import selectors

@login_required
def manage_budgets(request):
    if request.method == "POST":
        category_id = request.POST.get("category") or request.POST.get("category_id")
        amount_limit = str(request.POST.get("amount_limit", "0.00")).replace(",", ".")
        month_value = request.POST.get("month")
        year_value = request.POST.get("year")
        today = date.today()
        
        if not category_id:
            return redirect("manage_budgets")

        try:
            month = int(month_value) if month_value else today.month
        except (ValueError, TypeError):
            month = today.month
        try:
            year = int(year_value) if year_value else today.year
        except (ValueError, TypeError):
            year = today.year
        
        budget_service.create_threshold(
            user=request.user,
            category_id=int(category_id),
            amount_limit=float(amount_limit),
            month=month,
            year=year
        )
        return redirect("manage_budgets")

    budgets = request.user.budgets.all().select_related("category").order_by("-year", "-month", "category__name")
    paginator = Paginator(budgets, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "finance/manage_budgets.html", {
        "page_obj": page_obj,
        "categories": request.user.categories.all().order_by("name")
    })

@login_required
@require_POST
def create_budget(request):
    return manage_budgets(request)

@login_required
def edit_budget(request, budget_id):
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    if request.method == "POST":
        budget.amount_limit = Decimal(str(request.POST.get("amount_limit", "0.00")).replace(",", "."))
        try:
            budget.month = int(request.POST.get("month", budget.month))
        except (ValueError, TypeError):
            budget.month = budget.month
        try:
            budget.year = int(request.POST.get("year", budget.year))
        except (ValueError, TypeError):
            budget.year = budget.year
        budget.save()
        return redirect("manage_budgets")
    return render(request, "finance/edit_budget.html", {"budget": budget})

@login_required
def delete_budget(request, budget_id):
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    budget.delete()
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
        
    budget_status_report = selectors.get_monthly_budget_status(user=user, target_year=target_year, target_month=target_month)
    return JsonResponse({
        "status": "success", 
        "base_currency": getattr(user, "base_currency", "BRL"), 
        "budgets": budget_status_report
    })
