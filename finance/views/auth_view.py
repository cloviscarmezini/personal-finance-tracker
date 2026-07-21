from django.shortcuts import render, redirect
from django.contrib.auth import login as login_user, logout as logout_user, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.db import IntegrityError
from finance.models import User
from finance.services import category_service

def login_view(request):
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login_user(request, user)
                return redirect("index")
    else:
        form = AuthenticationForm()
    return render(request, "finance/login.html", {"form": form})

def logout_view(request):
    logout_user(request)
    return redirect("login")

def register(request):
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        base_currency = request.POST.get("base_currency", "BRL")
        password = request.POST.get("password", "")
        confirmation = request.POST.get("confirmation", "")

        if not username or not email or not password or not confirmation:
            return render(request, "finance/register.html", {"message": "All fields are required."})

        if password != confirmation:
            return render(request, "finance/register.html", {"message": "Passwords must match."})

        if User.objects.filter(username__iexact=username).exists():
            return render(request, "finance/register.html", {"message": "Username already taken."})

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            user.base_currency = base_currency
            user.save()

            category_service.reset_categories(user)
            
            login_user(request, user)
            return redirect("index")
        except IntegrityError:
            return render(request, "finance/register.html", {"message": "An error occurred during registration."})

    return render(request, "finance/register.html")
