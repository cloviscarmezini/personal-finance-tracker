from dataclasses import dataclass

@dataclass(frozen=True)
class TransactionResponseDTO:
    id: int
    date: str
    wallet_name: str
    wallet_currency: str
    category_name: str
    category_color: str
    category_icon: str
    description: str
    amount: float
    amount_in_base_currency: float
    exchange_rate_used: float
    transaction_type: str
    edit_url: str
    delete_url: str

    def to_dict(self) -> dict:
        return self.__dict__
    