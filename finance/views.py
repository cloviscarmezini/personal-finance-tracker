from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST, require_GET
from decimal import Decimal
from django.contrib.auth.decorators import login_required

from . import selectors
from . import services
from .models import Transaction, Wallet, Category, Budget

ITEMS_PER_PAGE = 10

def index(request):
    if not request.user.is_authenticated:
        return redirect("login")
    user = request.user
    context = {
        "wallets": user.wallets.all(),
        "categories": user.categories.all(),
        "base_currency": user.base_currency,
        "net_worth": selectors.get_consolidated_net_worth(user), 
    }
    return render(request, "finance/index.html", context)

def login_view(request):
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username"), password=request.POST.get("password"))
        if user is not None:
            login(request, user)
            services.process_recurring_transactions(user)
            return redirect("index")
        return render(request, "finance/login.html", {"message": "Invalid username and/or password."})
    return render(request, "finance/login.html")

def logout_view(request):
    logout(request)
    return redirect("login")

def register(request):
    if request.method == "POST":
        pword = request.POST.get("password")
        if pword != request.POST.get("confirmation"):
            return render(request, "finance/register.html", {"message": "Passwords must match."})
        try:
            services.create_user_with_default_categories(
                request.POST.get("username"), request.POST.get("email"), 
                pword, request.POST.get("base_currency", "BRL")
            )
            return redirect("index")
        except Exception:
            return render(request, "finance/register.html", {"message": "Username already taken."})
    return render(request, "finance/register.html")

@login_required
@require_POST
def create_transaction(request):
    wallet_id = request.POST.get("wallet")
    category_id = request.POST.get("category")
    t_type = request.POST.get("transaction_type")
    amount = Decimal(request.POST.get("amount", "0.00"))
    description = request.POST.get("description", "")
    t_date = request.POST.get("date")
    
    transaction = services.execute_financial_transaction(
        user=request.user,
        wallet_id=wallet_id,
        category_id=category_id,
        t_type=t_type,
        amount=amount,
        description=description,
        t_date=t_date
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return JsonResponse({
            "status": "success",
            "transaction": {
                "id": transaction.id,
                "date": str(transaction.date),
                "wallet_name": transaction.wallet.name,
                "wallet_currency": transaction.wallet.currency,
                "category_name": transaction.category.name if transaction.category else "Uncategorized",
                "category_color": transaction.category.color if transaction.category else "#adb5bd",
                "category_icon": transaction.category.icon if transaction.category else "bi-question-circle",
                "description": transaction.description,
                "amount": float(transaction.amount),
                "transaction_type": transaction.transaction_type,
                "edit_url": f"/manage/transactions/edit/{transaction.id}",
                "delete_url": f"/manage/transactions/delete/{transaction.id}"
            }
        })
        
    return redirect("index")

def manage_transactions(request):
    if not request.user.is_authenticated:
        return redirect("login")
        
    user = request.user
    queryset = Transaction.objects.filter(wallet__user=user)

    wallet_filter = request.GET.get("wallet")
    if wallet_filter:
        queryset = queryset.filter(wallet_id=wallet_filter)

    category_filter = request.GET.get("category")
    if category_filter:
        if category_filter == "uncategorized":
            queryset = queryset.filter(category__isnull=True)
        else:
            queryset = queryset.filter(category_id=category_filter)

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)

    min_amount = request.GET.get("min_amount")
    max_amount = request.GET.get("max_amount")
    if min_amount:
        queryset = queryset.filter(amount__gte=Decimal(min_amount))
    if max_amount:
        queryset = queryset.filter(amount__lte=Decimal(max_amount))

    order = request.GET.get("order", "-date") 
    if order == "price_high":
        queryset = queryset.order_by("-amount")
    elif order == "price_low":
        queryset = queryset.order_by("amount")
    elif order == "date_asc":
        queryset = queryset.order_by("date", "id")
    else: 
        queryset = queryset.order_by("-date", "-id")

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "wallets": user.wallets.all(),
        "categories": user.categories.all(),
        "current_filters": request.GET.dict()
    }
    return render(request, "finance/manage_transactions.html", context)

def edit_transaction(request, transaction_id):
    if not request.user.is_authenticated:
        return redirect("login")
        
    transaction = get_object_or_404(Transaction, id=transaction_id, wallet__user=request.user)
    
    if request.method == "POST":
        transaction.description = request.POST.get("description")
        if request.POST.get("category"):
            transaction.category_id = request.POST.get("category")
        else:
            transaction.category = None
        transaction.save()
        return redirect("manage_transactions")

    context = {
        "transaction": transaction,
        "categories": request.user.categories.all()
    }
    return render(request, "finance/edit_transaction.html", context)

def delete_transaction_view(request, transaction_id):
    if not request.user.is_authenticated:
        return redirect("login")
        
    transaction = get_object_or_404(Transaction, id=transaction_id, wallet__user=request.user)
    wallet = transaction.wallet
    
    if transaction.transaction_type == "INFLOW":
        wallet.balance -= transaction.amount
    else:
        wallet.balance += transaction.amount
        
    wallet.save()
    transaction.delete()
    return redirect("manage_transactions")

@require_POST
def api_create_wallet(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    name = request.POST.get("name")
    currency = request.POST.get("currency")
    if not name or not currency:
        return JsonResponse({"status": "error", "message": "Missing arguments"}, status=400)
    services.create_wallet(request.user, name, currency)
    return JsonResponse({"status": "success", "message": "Wallet created successfully"})

@require_POST
def api_create_category(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    name = request.POST.get("name")
    color = request.POST.get("color", "#6c757d")
    icon = request.POST.get("icon", "bi-tag")
    if not name:
        return JsonResponse({"status": "error", "message": "Missing arguments"}, status=400)
    services.create_category(request.user, name, color, icon)
    return JsonResponse({"status": "success", "message": "Category created successfully"})

@require_POST
def api_create_budget(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    category_id = request.POST.get("category")
    amount_limit = request.POST.get("amount_limit")
    month = request.POST.get("month")
    year = request.POST.get("year")
    if not category_id or not amount_limit or not month or not year:
        return JsonResponse({"status": "error", "message": "Missing arguments"}, status=400)
    services.create_budget(request.user, category_id, float(amount_limit), int(month), int(year))
    return JsonResponse({"status": "success", "message": "Budget created successfully"})

@require_GET
def get_chart_data(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    data = selectors.get_monthly_chart_data(request.user)
    return JsonResponse({
        "labels": data["labels"],
        "datasets": [{"data": data["datasets_data"], "backgroundColor": data["colors"]}]
    })

@require_GET
def get_budget_status(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    return JsonResponse({"budgets": selectors.get_monthly_budget_status(request.user)})

def manage_wallets(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if request.method == "POST":
        services.create_wallet(request.user, request.POST.get("name"), request.POST.get("currency"))
        return redirect("manage_wallets")
    wallets_list = Wallet.objects.filter(user=request.user).order_index("-created_at") if hasattr(Wallet.objects, 'order_index') else Wallet.objects.filter(user=request.user).order_by("-created_at")
    paginator = Paginator(wallets_list, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "finance/manage_wallets.html", {"page_obj": page_obj})

def edit_wallet(request, wallet_id):
    if not request.user.is_authenticated:
        return redirect("login")
    wallet = get_object_or_404(Wallet, id=wallet_id, user=request.user)
    if request.method == "POST":
        services.update_wallet(request.user, wallet_id, request.POST.get("name"), request.POST.get("currency"))
        return redirect("manage_wallets")
    return render(request, "finance/edit_wallet.html", {"wallet": wallet})

def delete_wallet_view(request, wallet_id):
    if not request.user.is_authenticated:
        return redirect("login")
    services.delete_wallet(request.user, wallet_id)
    return redirect("manage_wallets")

def manage_categories(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if request.method == "POST":
        services.create_category(request.user, request.POST.get("name"), request.POST.get("color"), request.POST.get("icon"))
        return redirect("manage_categories")
    categories_list = Category.objects.filter(user=request.user).order_by("name")
    paginator = Paginator(categories_list, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "finance/manage_categories.html", {"page_obj": page_obj})

def edit_category(request, category_id):
    if not request.user.is_authenticated:
        return redirect("login")
    category = get_object_or_404(Category, id=category_id, user=request.user)
    if request.method == "POST":
        services.update_category(request.user, category_id, request.POST.get("name"), request.POST.get("color"), request.POST.get("icon"))
        return redirect("manage_categories")
    return render(request, "finance/edit_category.html", {"category": category})

def delete_category_view(request, category_id):
    if not request.user.is_authenticated:
        return redirect("login")
    services.delete_category(request.user, category_id)
    return redirect("manage_categories")

def reset_categories_view(request):
    if not request.user.is_authenticated:
        return redirect("login")
    
    if request.method == "POST":
        services.reset_user_categories(request.user)
        
    return redirect("manage_categories")

def manage_budgets(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if request.method == "POST":
        services.create_budget(request.user, request.POST.get("category"), request.POST.get("amount_limit"), request.POST.get("month"), request.POST.get("year"))
        return redirect("manage_budgets")
    budgets_list = Budget.objects.filter(user=request.user).order_by("-year", "-month")
    paginator = Paginator(budgets_list, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "finance/manage_budgets.html", {"page_obj": page_obj, "categories": request.user.categories.all()})

def edit_budget(request, budget_id):
    if not request.user.is_authenticated:
        return redirect("login")
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    if request.method == "POST":
        services.update_budget(request.user, budget_id, request.POST.get("amount_limit"), request.POST.get("month"), request.POST.get("year"))
        return redirect("manage_budgets")
    return render(request, "finance/edit_budget.html", {"budget": budget})

def delete_budget_view(request, budget_id):
    if not request.user.is_authenticated:
        return redirect("login")
    services.delete_budget(request.user, budget_id)
    return redirect("manage_budgets")
