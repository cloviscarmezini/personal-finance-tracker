from finance.models import Wallet
from finance.dtos.wallet_dto import WalletResponseDTO


class WalletMapper:
    @staticmethod
    def to_response_dto(wallet: Wallet) -> WalletResponseDTO:
        return WalletResponseDTO(
            id=wallet.id,
            name=wallet.name,
            currency=wallet.currency,
            balance=float(wallet.balance),
            edit_url=f"/manage/wallets/edit/{wallet.id}",
            delete_url=f"/manage/wallets/delete/{wallet.id}"
        )
