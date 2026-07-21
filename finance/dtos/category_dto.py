from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryResponseDTO:
    id: int
    name: str
    color: str
    icon: str
    edit_url: str
    delete_url: str

    def to_dict(self) -> dict:
        return self.__dict__
