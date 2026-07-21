from finance.models import Budget
from finance.dtos.budget_dto import BudgetResponseDTO


class BudgetMapper:
    @staticmethod
    def to_response_dto(budget: Budget) -> BudgetResponseDTO:
        return BudgetResponseDTO(
            id=budget.id,
            category_id=budget.category.id,
            category_name=budget.category.name,
            amount_limit=float(budget.amount_limit),
            month=budget.month,
            year=budget.year,
            edit_url=f"/manage/budgets/edit/{budget.id}",
            delete_url=f"/manage/budgets/delete/{budget.id}"
        )
