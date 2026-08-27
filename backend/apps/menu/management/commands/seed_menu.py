"""
Popula o cardápio com itens realistas já classificados fiscalmente (Simples Nacional).
Uso: python manage.py seed_menu
"""
from django.core.management.base import BaseCommand

from apps.menu.models import MenuCategory, MenuItem

CATEGORIAS = [
    ('Parrilla', 10), ('Guarnições', 20), ('Entradas', 5),
    ('Bebidas sem álcool', 30), ('Cervejas', 40), ('Vinhos', 50), ('Cafés e Doces', 60),
]

ITENS = [
    # (categoria, nome, setor, preço, sku, gtin, ncm, cest, cfop, csosn, un)
    ('Parrilla', 'Bife de Chorizo 350g', 'PARRILLA', '89.90', 'PAR-CHORIZO-350', '', '02013000', '', '5101', '102', 'UN'),
    ('Parrilla', 'Ancho 400g', 'PARRILLA', '99.90', 'PAR-ANCHO-400', '', '02013000', '', '5101', '102', 'UN'),
    ('Parrilla', 'Costela no rolo (kg)', 'PARRILLA', '129.90', 'PAR-COSTELA-KG', '', '02013000', '', '5101', '102', 'KG'),
    ('Parrilla', 'Linguiça artesanal', 'PARRILLA', '39.90', 'PAR-LINGUICA', '', '16010000', '', '5101', '102', 'PT'),
    ('Guarnições', 'Batatas rústicas', 'COZINHA', '24.90', 'GUA-BATATA-RUST', '', '20052000', '', '5101', '102', 'PT'),
    ('Guarnições', 'Arroz biro-biro', 'COZINHA', '22.90', 'GUA-ARROZ-BIRO', '', '19022000', '', '5101', '102', 'PT'),
    ('Guarnições', 'Farofa da casa', 'COZINHA', '16.90', 'GUA-FAROFA', '', '19019090', '', '5101', '102', 'PT'),
    ('Entradas', 'Provoleta na chapa', 'PARRILLA', '44.90', 'ENT-PROVOLETA', '', '04061090', '', '5101', '102', 'UN'),
    ('Entradas', 'Chimichurri (pote 100g)', 'COZINHA', '9.90', 'ENT-CHIMI-100', '', '21039021', '', '5102', '102', 'UN'),
    ('Bebidas sem álcool', 'Água mineral 500ml', 'BAR', '6.00', 'BEB-AGUA-500', '7891910000147', '22011000', '0300700', '5405', '500', 'UN'),
    ('Bebidas sem álcool', 'Refrigerante lata 350ml', 'BAR', '8.00', 'BEB-REFRI-350', '7894900011517', '22021000', '0300800', '5405', '500', 'UN'),
    ('Bebidas sem álcool', 'Suco natural laranja 300ml', 'BAR', '12.00', 'BEB-SUCO-LAR-300', '', '20091200', '', '5102', '102', 'UN'),
    ('Cervejas', 'Chopp Pilsen 500ml', 'BAR', '16.00', 'CER-CHOPP-500', '', '22030000', '0301100', '5405', '500', 'UN'),
    ('Cervejas', 'Cerveja long neck 355ml', 'BAR', '14.00', 'CER-LN-355', '7891149102037', '22030000', '0301100', '5405', '500', 'UN'),
    ('Vinhos', 'Malbec taça 150ml', 'BAR', '29.00', 'VIN-MALBEC-TACA', '', '22042100', '0302200', '5405', '500', 'UN'),
    ('Vinhos', 'Malbec garrafa 750ml', 'BAR', '169.00', 'VIN-MALBEC-750', '', '22042100', '0302200', '5405', '500', 'GF'),
    ('Cafés e Doces', 'Café espresso', 'BAR', '7.00', 'CAF-ESPRESSO', '', '21011110', '', '5102', '102', 'UN'),
    ('Cafés e Doces', 'Pudim de leite', 'COZINHA', '18.00', 'DOC-PUDIM', '', '19053100', '', '5101', '102', 'UN'),
]


class Command(BaseCommand):
    help = 'Popula o cardápio com itens de exemplo classificados fiscalmente.'

    def handle(self, *args, **options):
        cats = {}
        for nome, ordem in CATEGORIAS:
            cat, _ = MenuCategory.objects.get_or_create(name=nome, defaults={'display_order': ordem})
            cats[nome] = cat
        self.stdout.write(self.style.SUCCESS(f'{len(cats)} categorias.'))

        criados = 0
        for (cat, nome, setor, preco, sku, gtin, ncm, cest, cfop, csosn, un) in ITENS:
            obj, created = MenuItem.objects.get_or_create(sku=sku, defaults=dict(
                category=cats[cat], name=nome, sector=setor, price=preco,
                barcode_gtin=gtin, ncm=ncm, cest=cest, cfop=cfop, csosn=csosn,
                unit_commercial=un, unit_taxable=un, origem='0',
                pis_cst='49', cofins_cst='49',
            ))
            criados += int(created)
        self.stdout.write(self.style.SUCCESS(f'{criados} itens novos ({MenuItem.objects.count()} no total).'))
        self.stdout.write('Rode a conferência: GET /api/menu/items/fiscal_report/')
