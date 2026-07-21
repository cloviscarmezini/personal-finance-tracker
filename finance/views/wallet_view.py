from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.http import Http404
from finance.models import Wallet
from finance.services import wallet_service


@login_required
def manage_wallets(request):
    if request.method == "POST":
        try:
            wallet_service.create_wallet(
                user=request.user,
                name=request.POST.get("name"),
                currency=request.POST.get("currency", "BRL"),
                balance=request.POST.get("balance", "0.00"),
            )
        except (ValidationError, ValueError):
            return redirect(request.META.get("HTTP_REFERER", "manage_wallets"))
        return redirect("manage_wallets")

    wallets = wallet_service.list_wallets(request.user)
    paginator = Paginator(wallets, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "finance/manage_wallets.html", {
        "page_obj": page_obj,
        "base_currency": getattr(request.user, "base_currency", "BRL")
    })

@login_required
@require_POST
def create_wallet(request):
    return manage_wallets(request)

@login_required
def edit_wallet(request, wallet_id):
    try:
        wallet = wallet_service.get_wallet(request.user, wallet_id)
    except (Wallet.DoesNotExist, ValidationError, ValueError):
        raise Http404("Wallet not found")

    if request.method == "POST":
        try:
            wallet_service.update_wallet(
                wallet_id=wallet_id,
                user=request.user,
                name=request.POST.get("name"),
                currency=request.POST.get("currency"),
            )
        except (ValidationError, ValueError):
            return redirect(request.META.get("HTTP_REFERER", "manage_wallets"))
        return redirect("manage_wallets")
    return render(request, "finance/edit_wallet.html", {"wallet": wallet})

@login_required
def delete_wallet(request, wallet_id):
    try:
        wallet_service.get_wallet(request.user, wallet_id)
    except (Wallet.DoesNotExist, ValidationError, ValueError):
        raise Http404("Wallet not found")
    wallet_service.delete_wallet(wallet_id=wallet_id, user=request.user)
    return redirect("manage_wallets")
