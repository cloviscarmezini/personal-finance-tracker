from finance.models import Wallet
from finance.services import exchange_service
from decimal import Decimal

def get_consolidated_net_worth(user) -> Decimal:
    wallets = Wallet.objects.filter(user=user)
    total_net_worth = Decimal("0.00")
    for wallet in wallets:
        rate = exchange_service.get_pair_rate(wallet.currency, user.base_currency)
        total_net_worth += wallet.balance * rate
    return total_net_worth
