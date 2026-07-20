from django.core.management.base import BaseCommand
from finance.models import Category

class Command(BaseCommand):
    help = "Seeds the database with system-wide default financial categories"

    def handle(self, *args, **kwargs):
        default_categories = [
            ("Food & Dining", "#ff6384", "bi-egg-fried"),
            ("Housing & Rent", "#36a2eb", "bi-house-door"),
            ("Transport", "#cc65fe", "bi-car-front"),
            ("Salary / Income", "#4bc0c0", "bi-cash-coin")
        ]
        
        created_count = 0
        for name, color, icon in default_categories:
            obj, created = Category.objects.get_or_create(
                name=name,
                is_system_default=True,
                defaults={"color": color, "icon": icon, "user": None}
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_count} default system categories."))