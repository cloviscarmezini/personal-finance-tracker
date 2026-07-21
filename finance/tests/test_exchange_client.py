from django.test import TestCase, override_settings
from unittest.mock import patch
from decimal import Decimal
from finance.clients.exchange_client import ExchangeRateClient


class ExchangeClientTestCase(TestCase):
    def test_fetch_live_pair_rate_raises_without_api_key(self):
        client = ExchangeRateClient(api_key="")
        with self.assertRaises(ValueError):
            client.fetch_live_pair_rate("USD", "BRL")

    @patch("finance.clients.exchange_client.requests.get")
    def test_fetch_live_pair_rate_returns_decimal_on_success(self, mock_get):
        mock_get.return_value.json.return_value = {
            "result": "success",
            "conversion_rate": 5.1234
        }
        mock_get.return_value.status_code = 200
        client = ExchangeRateClient(api_key="dummy")
        rate = client.fetch_live_pair_rate("USD", "BRL")
        self.assertEqual(rate, Decimal("5.1234"))

    @patch("finance.clients.exchange_client.requests.get")
    def test_fetch_live_pair_rate_raises_io_error_on_api_failure(self, mock_get):
        mock_get.return_value.json.return_value = {
            "result": "error",
            "error-type": "invalid-key"
        }
        mock_get.return_value.status_code = 400
        client = ExchangeRateClient(api_key="dummy")
        with self.assertRaises(IOError):
            client.fetch_live_pair_rate("USD", "BRL")
