from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from finance.models import Wallet, Category


class ViewsLayerTestCase(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username="viewuser", password="pass")
        self.category = Category.objects.create(user=self.user, name="Auto", color="#000000", icon="bi-car")
        self.wallet = Wallet.objects.create(user=self.user, name="Primary", currency="BRL", balance=Decimal("50.00"))

    def test_register_page_get(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "finance/register.html")

    def test_register_post_creates_user(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser",
            "email": "newuser@example.com",
            "base_currency": "USD",
            "password": "securepass",
            "confirmation": "securepass"
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.User.objects.filter(username="newuser").exists())

    def test_manage_wallets_requires_login(self):
        response = self.client.get(reverse("manage_wallets"))
        self.assertEqual(response.status_code, 302)

    def test_manage_wallets_authenticated(self):
        self.client.login(username="viewuser", password="pass")
        response = self.client.get(reverse("manage_wallets"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "finance/manage_wallets.html")

    def test_create_wallet_view(self):
        self.client.login(username="viewuser", password="pass")
        response = self.client.post(reverse("create_wallet"), {
            "name": "Secondary",
            "currency": "USD",
            "balance": "25.00"
        })
        self.assertRedirects(response, reverse("manage_wallets"))
        self.assertTrue(Wallet.objects.filter(name="Secondary", user=self.user).exists())

    def test_create_category_view(self):
        self.client.login(username="viewuser", password="pass")
        response = self.client.post(reverse("create_category"), {
            "name": "Fitness",
            "color": "#123456",
            "icon": "bi-heart"
        })
        self.assertRedirects(response, reverse("manage_categories"))
        self.assertTrue(Category.objects.filter(name="Fitness", user=self.user).exists())

    def test_get_currencies_api(self):
        response = self.client.get(reverse("api_get_currencies"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "success", "currencies": response.json()["currencies"]})

    def test_get_balance_metrics_requires_login(self):
        response = self.client.get(reverse("api_analytics_balance_metrics"))
        self.assertEqual(response.status_code, 302)

    def test_get_chart_data_requires_login(self):
        response = self.client.get(reverse("api_analytics_chart"))
        self.assertEqual(response.status_code, 302)

    def test_update_base_currency_redirects(self):
        self.client.login(username="viewuser", password="pass")
        response = self.client.post(reverse("update_base_currency"), {"base_currency": "EUR"}, HTTP_REFERER=reverse("manage_wallets"))
        self.assertRedirects(response, reverse("manage_wallets"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.base_currency, "EUR")
