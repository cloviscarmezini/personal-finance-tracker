import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction as db_transaction
from finance.models import Wallet, Category
from finance import services

class Command(BaseCommand):
    help = "Seeds the database with a test user, multi-currency wallets, and 4 months of structured transactions."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Starting deterministic ledger seeding pipeline..."))

        # 1. MONKEY PATCHING DE SEGURANÇA: Intercepta o cliente de câmbio para evitar o TypeError no services.py
        original_get_pair_rate = services.exchange_client.get_pair_rate
        
        # Sobrescreve temporariamente o método para garantir que retorne Decimal
        def patched_get_pair_rate(from_curr, to_curr):
            rate = original_get_pair_rate(from_curr, to_curr)
            return Decimal(str(rate))
            
        services.exchange_client.get_pair_rate = patched_get_pair_rate

        # Obtém o modelo de usuário ativo
        User = get_user_model()

        username = "test"
        email = "test@harvard.edu"
        password = "test"
        base_currency = "USD"

        try:
            with db_transaction.atomic():
                # 2. Limpeza ou criação do usuário de teste
                User.objects.filter(username=username).delete()
                user = User.objects.create_user(
                    username=username, 
                    email=email, 
                    password=password
                )
                
                user.base_currency = base_currency
                user.save()
                
                # Coleta ou gera categorias defaults
                categories = list(Category.objects.filter(user=user))
                if not categories:
                    core_cats = [
                        {"name": "Housing", "color": "#0d6efd", "icon": "bi-house"},
                        {"name": "Food & Dining", "color": "#198754", "icon": "bi-egg-fried"},
                        {"name": "Cloud Architecture", "color": "#6f42c1", "icon": "bi-cloud"},
                        {"name": "Salary & Invoices", "color": "#ffc107", "icon": "bi-wallet2"}
                    ]
                    for cat_data in core_cats:
                        categories.append(
                            Category.objects.create(user=user, **cat_data)
                        )

                # 3. Instanciação das 3 Wallets
                wallet_templates = [
                    {"name": "Silicon Valley Checking", "currency": "USD", "balance": Decimal("12500.00")},
                    {"name": "São Paulo Daily Hub", "currency": "BRL", "balance": Decimal("45000.00")},
                    {"name": "Euro Travel Ledger", "currency": "EUR", "balance": Decimal("8200.00")}
                ]
                
                wallets = []
                for w_data in wallet_templates:
                    wallet = Wallet.objects.create(
                        user=user,
                        name=w_data["name"],
                        currency=w_data["currency"],
                        balance=w_data["balance"]
                    )
                    wallets.append(wallet)

                # 4. Definição da Matrix Temporal Dinâmica (Janela de 4 Meses)
                today = date.today()
                start_date = (today - timedelta(days=60)).replace(day=1)
                next_month_date = (today + timedelta(days=45)).replace(day=28)
                total_days = (next_month_date - start_date).days

                descriptions_outflow = [
                    "AWS Cloud Infrastructure Bill", "GitHub Enterprise Seat", 
                    "Uber Eats Business Dinner", "Starbucks Synergy Coffee", 
                    "Office Co-working Rent", "Gym Membership", "Internet Fiber Subscription"
                ]
                descriptions_inflow = [
                    "Monthly SaaS Subscription Payout", "Contract Engineering Milestone", 
                    "AdSense Yield Revenue", "Consulting Retainer Invoice"
                ]

                self.stdout.write(f"Generating random transactions between {start_date} and {next_month_date}...")

                # 5. Loop de alimentação de registros
                transaction_count = 0
                for wallet in wallets:
                    num_transactions = random.randint(15, 25)
                    
                    for _ in range(num_transactions):
                        random_days_offset = random.randint(0, total_days)
                        t_date = start_date + timedelta(days=random_days_offset)
                        
                        t_type = "OUTFLOW" if random.random() < 0.75 else "INFLOW"
                        
                        if t_type == "OUTFLOW":
                            description = random.choice(descriptions_outflow)
                            amount_str = f"{random.uniform(15.50, 450.00):.2f}"
                            category = random.choice([c for c in categories if c.name != "Salary & Invoices"])
                        else:
                            description = random.choice(descriptions_inflow)
                            amount_str = f"{random.uniform(1200.00, 5000.00):.2f}"
                            category = Category.objects.filter(user=user, name="Salary & Invoices").first() or random.choice(categories)

                        amount = Decimal(amount_str)

                        # Dispara pelo Service Layer centralizado de forma segura
                        services.execute_financial_transaction(
                            user=user,
                            wallet_id=wallet.id,
                            category_id=category.id if category else None,
                            t_type=t_type,
                            amount=amount,
                            description=description,
                            t_date=t_date
                        )
                        transaction_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully seeded database!\n"
                    f"User created -> Username: '{username}' | Password: '{password}'\n"
                    f"Created 3 multi-currency wallets and {transaction_count} transactions across a 4-month dynamic timeline."
                )
            )

        finally:
            # Restaurar o método original do cliente após o término do comando
            services.exchange_client.get_pair_rate = original_get_pair_rate
            