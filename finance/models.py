from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    base_currency = models.CharField(max_length=3, default="BRL")

class Wallet(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallets")
    name = models.CharField(max_length=50)
    currency = models.CharField(max_length=3, default="BRL")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

class Category(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories", null=True, blank=True)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#6c757d")
    icon = models.CharField(max_length=50, default="bi-tag")
    is_system_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Categories"

class Budget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="budgets")
    amount_limit = models.DecimalField(max_digits=12, decimal_places=2)
    month = models.IntegerField()
    year = models.IntegerField()

class Transaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name="transactions", null=True, blank=True)
    transaction_type = models.CharField(max_length=7, choices=[("INFLOW", "Inflow"), ("OUTFLOW", "Outflow")])
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_in_base_currency = models.DecimalField(max_digits=12, decimal_places=2)
    exchange_rate_used = models.DecimalField(max_digits=10, decimal_places=4)
    description = models.CharField(max_length=200)
    date = models.DateField()
    is_recurring = models.BooleanField(default=False)
    next_due_date = models.DateField(null=True, blank=True)
    