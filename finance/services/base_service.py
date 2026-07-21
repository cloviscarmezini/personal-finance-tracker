from datetime import date
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError


class BaseService:
    @staticmethod
    def _parse_int(value, field_name="value", default=None, minimum=None, maximum=None):
        if value is None or str(value).strip() == "":
            if default is not None:
                return default
            raise ValidationError(f"{field_name.capitalize()} is required.")
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            raise ValidationError(f"{field_name.capitalize()} must be a valid integer.")
        if minimum is not None and parsed < minimum:
            raise ValidationError(f"{field_name.capitalize()} must be at least {minimum}.")
        if maximum is not None and parsed > maximum:
            raise ValidationError(f"{field_name.capitalize()} must be at most {maximum}.")
        return parsed

    @staticmethod
    def _parse_decimal(value, field_name="value"):
        if value is None or str(value).strip() == "":
            raise ValidationError(f"{field_name.replace('_', ' ').capitalize()} is required.")
        try:
            return Decimal(str(value).replace(",", "."))
        except (InvalidOperation, TypeError):
            raise ValidationError(f"{field_name.replace('_', ' ').capitalize()} must be a valid number.")

    @staticmethod
    def _parse_decimal_optional(value, field_name="value"):
        if value is None or str(value).strip() == "":
            return None
        return BaseService._parse_decimal(value, field_name)

    @staticmethod
    def _parse_date(value, field_name="date"):
        if value is None or str(value).strip() == "":
            raise ValidationError(f"{field_name.capitalize()} is required.")
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except (TypeError, ValueError):
            raise ValidationError(f"{field_name.capitalize()} must be a valid date in YYYY-MM-DD format.")

    @staticmethod
    def _normalize_name(name):
        name_value = str(name or "").strip()
        if not name_value:
            raise ValidationError("Name is required.")
        return name_value

