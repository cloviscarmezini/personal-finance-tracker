from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.http import Http404
from django.core.paginator import Paginator
from finance.models import Category
from finance.services import category_service

CORE_CATEGORY_TEMPLATE = [
    {"name": "Housing", "color": "#0d6efd", "icon": "bi-house"},
    {"name": "Food & Dining", "color": "#198754", "icon": "bi-egg-fried"},
    {"name": "Cloud Architecture", "color": "#6f42c1", "icon": "bi-cloud"},
    {"name": "Salary & Invoices", "color": "#ffc107", "icon": "bi-wallet2"}
]


@login_required
def manage_categories(request):
    if request.method == "POST":
        try:
            category_service.create_category(
                user=request.user,
                name=request.POST.get("name"),
                color=request.POST.get("color", "#6c757d"),
                icon=request.POST.get("icon", "bi-tag"),
            )
        except (ValidationError, ValueError):
            return redirect(request.META.get("HTTP_REFERER", "manage_categories"))
        return redirect("manage_categories")

    categories = category_service.list_categories(request.user)
    paginator = Paginator(categories, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "finance/manage_categories.html", {
        "page_obj": page_obj
    })

@login_required
@require_POST
def create_category(request):
    return manage_categories(request)

@login_required
def edit_category(request, category_id):
    try:
        category = category_service.get_category(request.user, category_id)
    except Category.DoesNotExist:
        raise Http404("Category not found")

    if request.method == "POST":
        try:
            category_service.update_category(
                category_id=category_id,
                user=request.user,
                name=request.POST.get("name"),
                color=request.POST.get("color"),
                icon=request.POST.get("icon"),
            )
        except (ValidationError, ValueError):
            return redirect(request.META.get("HTTP_REFERER", "manage_categories"))
        return redirect("manage_categories")
    return render(request, "finance/edit_category.html", {"category": category})

@login_required
def delete_category(request, category_id):
    try:
        category_service.get_category(request.user, category_id)
    except Category.DoesNotExist:
        raise Http404("Category not found")
    category_service.delete_category(category_id=category_id, user=request.user)
    return redirect("manage_categories")

@login_required
@require_POST
def reset_categories(request):
    category_service.reset_categories(request.user, CORE_CATEGORY_TEMPLATE)
    return redirect("manage_categories")
