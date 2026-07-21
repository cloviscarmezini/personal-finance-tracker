from django.db import transaction as db_transaction
from finance.models import Category
from finance.services.base_service import BaseService


class CategoryService(BaseService):
    @staticmethod
    def _normalize_color(color):
        return str(color or "#6c757d").strip()

    @staticmethod
    def _normalize_icon(icon):
        return str(icon or "bi-tag").strip()

    @db_transaction.atomic
    def create_category(self, user, name, color, icon):
        return Category.objects.create(
            user=user,
            name=self._normalize_name(name),
            color=self._normalize_color(color),
            icon=self._normalize_icon(icon),
        )

    @db_transaction.atomic
    def update_category(self, category_id, user, name, color, icon):
        category = Category.objects.get_for_user(user, category_id)
        category.name = self._normalize_name(name)
        category.color = self._normalize_color(color)
        category.icon = self._normalize_icon(icon)
        category.save()
        return category

    @db_transaction.atomic
    def delete_category(self, category_id, user):
        category = Category.objects.get_for_user(user, category_id)
        category.delete()

    @db_transaction.atomic
    def reset_categories(self, user, core_categories):
        Category.objects.filter(user=user).delete()
        created = []
        for cat_data in core_categories:
            created.append(Category.objects.create(user=user, **cat_data))
        return created

    def list_categories(self, user):
        return Category.objects.for_user(user)

    def get_category(self, user, category_id):
        return Category.objects.get_for_user(user, category_id)
