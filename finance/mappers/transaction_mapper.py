from finance.models import Transaction
from finance.dtos.transaction_dto import TransactionResponseDTO

class TransactionMapper:
    @staticmethod
    def to_response_dto(transaction: Transaction) -> TransactionResponseDTO:
        category_name = transaction.category.name if transaction.category else "Uncategorized"
        category_color = transaction.category.color if transaction.category else "#adb5bd"
        category_icon = transaction.category.icon if transaction.category else "bi-question-circle"
        
        return TransactionResponseDTO(
            id=transaction.id,
            date=str(transaction.date),
            wallet_name=transaction.wallet.name,
            wallet_currency=transaction.wallet.currency,
            category_name=category_name,
            category_color=category_color,
            category_icon=category_icon,
            description=transaction.description,
            amount=float(transaction.amount),
            amount_in_base_currency=float(transaction.amount_in_base_currency),
            exchange_rate_used=float(transaction.exchange_rate_used),
            transaction_type=transaction.transaction_type,
            edit_url=f"/manage/transactions/edit/{transaction.id}",
            delete_url=f"/manage/transactions/delete/{transaction.id}"
        )
    