from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetResponseDTO:
    id: int
    category_id: int
    category_name: str
    amount_limit: float
    month: int
    year: int
    edit_url: str
    delete_url: str

    def to_dict(self) -> dict:
        return self.__dict__
