"""
Management command to seed initial data for Toca do Espanhol.
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.tables.models import Table
from apps.menu.models import MenuCategory, MenuItem

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds initial data: admin user and sample tables'

    def handle(self, *args, **options):
        self.stdout.write('🍖 Iniciando seed da Toca do Espanhol...\n')

        # Create admin user
        if not User.objects.filter(email='admin@toca.com').exists():
            User.objects.create_superuser(
                email='admin@toca.com',
                password='123456',
                name='Administrador',
                role='ADM_MAXIMO',
            )
            self.stdout.write(self.style.SUCCESS('✅ Admin criado: admin@toca.com / 123456'))
        else:
            self.stdout.write('ℹ️  Admin já existe.')

        # Create sample users
        sample_users = [
            {'email': 'gerente@toca.com', 'name': 'Carlos Gerente', 'role': 'GERENTE'},
            {'email': 'garcom@toca.com', 'name': 'João Garçom', 'role': 'GARCOM'},
            {'email': 'cozinha@toca.com', 'name': 'Maria Cozinheira', 'role': 'COZINHA'},
            {'email': 'parrilla@toca.com', 'name': 'Pedro Parrilla', 'role': 'PARRILLA'},
            {'email': 'caixa@toca.com', 'name': 'Ana Caixa', 'role': 'CAIXA'},
            {'email': 'recepcao@toca.com', 'name': 'Lucia Recepção', 'role': 'RECEPCAO'},
        ]
        for u in sample_users:
            if not User.objects.filter(email=u['email']).exists():
                User.objects.create_user(password='123456', **u)
                self.stdout.write(self.style.SUCCESS(f"✅ Usuário criado: {u['email']}"))

        # Create tables
        for n in range(1, 21):
            seats = 2 if n <= 4 else (6 if n >= 17 else 4)
            Table.objects.get_or_create(number=n, defaults={'seats': seats})
        self.stdout.write(self.style.SUCCESS('✅ 20 mesas criadas.'))

        # Create sample menu (categories + items) so Pedidos tem o que lançar
        categories = {
            'Pratos Principais': 1,
            'Bebidas': 2,
        }
        cat_objs = {}
        for name, order in categories.items():
            cat, _ = MenuCategory.objects.get_or_create(name=name, defaults={'display_order': order})
            cat_objs[name] = cat

        sample_items = [
            {'category': 'Pratos Principais', 'name': 'Picanha na Brasa', 'sector': 'PARRILLA',
             'price': '89.90', 'sku': 'PIC001', 'ncm': '02013000'},
            {'category': 'Pratos Principais', 'name': 'Costela Bovina', 'sector': 'PARRILLA',
             'price': '69.90', 'sku': 'COS001', 'ncm': '02013000'},
            {'category': 'Pratos Principais', 'name': 'Batata Frita', 'sector': 'COZINHA',
             'price': '24.90', 'sku': 'BAT001', 'ncm': '20041000'},
            {'category': 'Bebidas', 'name': 'Refrigerante Lata', 'sector': 'BAR',
             'price': '8.00', 'sku': 'REF001', 'ncm': '22021000'},
            {'category': 'Bebidas', 'name': 'Água Mineral', 'sector': 'BAR',
             'price': '6.00', 'sku': 'AGU001', 'ncm': '22011000'},
        ]
        for item in sample_items:
            category = cat_objs[item.pop('category')]
            MenuItem.objects.get_or_create(
                sku=item['sku'],
                defaults={**item, 'category': category},
            )
        self.stdout.write(self.style.SUCCESS('✅ Cardápio de exemplo criado (2 categorias, 5 itens).'))

        self.stdout.write(self.style.SUCCESS('\n🎉 Seed concluído com sucesso!\n'))
        self.stdout.write('Credenciais padrão (senha: 123456):')
        self.stdout.write('  admin@toca.com       → ADM_MAXIMO')
        self.stdout.write('  gerente@toca.com     → GERENTE')
        self.stdout.write('  garcom@toca.com      → GARCOM')
        self.stdout.write('  cozinha@toca.com     → COZINHA')
        self.stdout.write('  parrilla@toca.com    → PARRILLA')
        self.stdout.write('  caixa@toca.com       → CAIXA')
        self.stdout.write('  recepcao@toca.com    → RECEPCAO')
