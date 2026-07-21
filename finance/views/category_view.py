from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction as db_transaction
from django.core.paginator import Paginator
from finance.models import Category

@login_required
def manage_categories(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        color = request.POST.get("color", "#6c757d").strip()
        icon = request.POST.get("icon", "bi-tag").strip()

        if not name:
            return redirect("manage_categories")

        Category.objects.create(user=request.user, name=name, color=color, icon=icon)
        return redirect("manage_categories")

    categories = request.user.categories.all().order_by("name")
    paginator = Paginator(categories, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "finance/manage_categories.html", {
        "page_obj": page_obj
    })

@login_required
@require_POST
def create_category(request):
    name = request.POST.get("name", "").strip()
    color = request.POST.get("color", "#6c757d").strip()
    icon = request.POST.get("icon", "bi-tag").strip()

    if not name:
        return redirect("manage_categories")

    Category.objects.create(user=request.user, name=name, color=color, icon=icon)
    return redirect("manage_categories")

@login_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, user=request.user)
    if request.method == "POST":
        category.name = request.POST.get("name", category.name).strip()
        category.color = request.POST.get("color", category.color).strip()
        category.icon = request.POST.get("icon", category.icon).strip()
        category.save()
        return redirect("manage_categories")
    return render(request, "finance/edit_category.html", {"category": category})

@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, user=request.user)
    category.delete()
    return redirect("manage_categories")

@login_required
@require_POST
def reset_categories(request):
    user = request.user
    with db_transaction.atomic():
        Category.objects.filter(user=user).delete()
        core_cats = [
            {"name": "Housing", "color": "#0d6efd", "icon": "bi-house"},
            {"name": "Food & Dining", "color": "#198754", "icon": "bi-egg-fried"},
            {"name": "Cloud Architecture", "color": "#6f42c1", "icon": "bi-cloud"},
            {"name": "Salary & Invoices", "color": "#ffc107", "icon": "bi-wallet2"}
        ]
        for cat_data in core_cats:
            Category.objects.create(user=user, **cat_data)
    return redirect("manage_categories")
