from finance.models import Category
from finance.dtos.category_dto import CategoryResponseDTO


class CategoryMapper:
    @staticmethod
    def to_response_dto(category: Category) -> CategoryResponseDTO:
        return CategoryResponseDTO(
            id=category.id,
            name=category.name,
            color=category.color,
            icon=category.icon,
            edit_url=f"/manage/categories/edit/{category.id}",
            delete_url=f"/manage/categories/delete/{category.id}"
        )
