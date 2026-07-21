from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from decimal import Decimal
from finance.models import Wallet

@login_required
def manage_wallets(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        currency = request.POST.get("currency", "BRL").strip().upper()
        initial_balance = str(request.POST.get("balance", "0.00")).replace(",", ".")

        if not name:
            return redirect("manage_wallets")

        Wallet.objects.create(
            user=request.user,
            name=name,
            currency=currency,
            balance=Decimal(initial_balance)
        )
        return redirect("manage_wallets")

    wallets = request.user.wallets.all().order_by("-created_at")
    paginator = Paginator(wallets, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "finance/manage_wallets.html", {
        "page_obj": page_obj,
        "base_currency": getattr(request.user, "base_currency", "BRL")
    })

@login_required
@require_POST
def create_wallet(request):
    name = request.POST.get("name", "").strip()
    currency = request.POST.get("currency", "BRL").strip().upper()
    initial_balance = str(request.POST.get("balance", "0.00")).replace(",", ".")

    if not name:
        return redirect("manage_wallets")

    Wallet.objects.create(
        user=request.user,
        name=name,
        currency=currency,
        balance=Decimal(initial_balance)
    )
    return redirect("manage_wallets")

@login_required
def edit_wallet(request, wallet_id):
    wallet = get_object_or_404(Wallet, id=wallet_id, user=request.user)
    if request.method == "POST":
        wallet.name = request.POST.get("name", wallet.name).strip()
        wallet.currency = request.POST.get("currency", wallet.currency).strip().upper()
        wallet.balance = Decimal(str(request.POST.get("balance", wallet.balance)).replace(",", "."))
        wallet.save()
        return redirect("manage_wallets")
    return render(request, "finance/edit_wallet.html", {"wallet": wallet})

@login_required
def delete_wallet(request, wallet_id):
    wallet = get_object_or_404(Wallet, id=wallet_id, user=request.user)
    wallet.delete()
    return redirect("manage_wallets")
