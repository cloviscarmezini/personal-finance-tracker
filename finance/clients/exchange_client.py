import requests
from decimal import Decimal
from django.conf import settings

class ExchangeRateClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or getattr(settings, "EXCHANGE_RATE_API_KEY", "")
        self.base_url = "https://v6.exchangerate-api.com/v6"

    def fetch_live_pair_rate(self, from_currency: str, to_currency: str) -> Decimal:
        if not self.api_key:
            raise ValueError("Exchange Rate API Key is missing or invalid.")
        url = f"{self.base_url}/{self.api_key}/pair/{from_currency}/{to_currency}"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get("result") == "success":
            return Decimal(str(data.get("conversion_rate")))
        raise IOError(f"API Error: {data.get('error-type')}")
    