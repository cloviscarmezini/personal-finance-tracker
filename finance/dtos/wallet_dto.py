from dataclasses import dataclass


@dataclass(frozen=True)
class WalletResponseDTO:
    id: int
    name: str
    currency: str
    balance: float
    edit_url: str
    delete_url: str

    def to_dict(self) -> dict:
        return self.__dict__
