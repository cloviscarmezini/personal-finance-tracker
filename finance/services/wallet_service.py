from decimal import Decimal
from django.db import transaction as db_transaction
from finance.models import Wallet
from finance.services.base_service import BaseService


class WalletService(BaseService):
    @staticmethod
    def _normalize_currency(currency):
        currency_value = str(currency or "BRL").strip().upper()
        if len(currency_value) != 3:
            raise ValueError("Currency must be a 3-letter code.")
        return currency_value

    @db_transaction.atomic
    def create_wallet(self, user, name, currency, balance):
        return Wallet.objects.create(
            user=user,
            name=self._normalize_name(name),
            currency=self._normalize_currency(currency),
            balance=self._parse_decimal(balance, "balance")
        )

    @db_transaction.atomic
    def update_wallet(self, wallet_id, user, name, currency, balance=None):
        wallet = Wallet.objects.filter(id=wallet_id, user=user).first()
        if not wallet:
            raise Wallet.DoesNotExist("Wallet not found.")

        wallet.name = self._normalize_name(name)
        wallet.currency = self._normalize_currency(currency)
        if balance is not None and str(balance).strip() != "":
            wallet.balance = self._parse_decimal(balance, "balance")
        wallet.save()
        return wallet

    @db_transaction.atomic
    def delete_wallet(self, wallet_id, user):
        wallet_id_value = self._parse_int(wallet_id, "wallet_id")
        wallet = Wallet.objects.get_for_user(user, wallet_id_value)
        wallet.delete()

    def list_wallets(self, user):
        return Wallet.objects.for_user(user)

    def get_wallet(self, user, wallet_id):
        wallet_id_value = self._parse_int(wallet_id, "wallet_id")
        return Wallet.objects.get_for_user(user, wallet_id_value)

    def get_consolidated_net_worth(self, user, exchange_service):
        wallets = self.list_wallets(user)
        total_net_worth = Decimal("0.00")
        base_currency = getattr(user, "base_currency", "BRL").upper()
        for wallet in wallets:
            rate = exchange_service.get_pair_rate(wallet.currency, base_currency)
            total_net_worth += wallet.balance * rate
        return total_net_worth
