"""
Popula o cardápio.

- ITENS_EXEMPLO: itens de demonstração já classificados fiscalmente.
- CARDAPIO: o cardápio real do restaurante (Toca do Espanhol Parrilla),
  com os campos fiscais NCM, CFOP, CSOSN, Origem e PIS/COFINS já
  preenchidos conforme classificação PADRÃO para restaurantes optantes
  pelo Simples Nacional que vendem "produção própria" (pratos preparados
  na cozinha/parrilla para consumo no local), e não revenda de mercadoria
  de terceiros.

  ⚠️  ATENÇÃO — VALIDAR COM O CONTADOR ANTES DE EMITIR NFC-e REAL:
  Esta classificação segue o entendimento padrão do setor (o mesmo usado
  por sistemas como SisFood/Sischef para churrascarias/restaurantes no
  Simples Nacional), mas:
    1. Alíquotas de ICMS e regras de substituição tributária variam por
       estado — confirme as regras vigentes para o Rio de Janeiro/Maricá.
    2. A reforma tributária (transição 2026-2033, IBS/CBS) está mudando
       tabelas de CFOP/CST ao longo do tempo — reconfirme periodicamente.
    3. A "Origem" (campo 0 = nacional) dos cortes anunciados como "de
       origem argentina" (Bife Ancho, Bife de Chorizo, T'Bone) foi
       classificada como nacional por se tratar de produção própria do
       estabelecimento (a carne é transformada em prato pronto, não
       revendida como mercadoria importada) — este é o ponto de maior
       divergência de interpretação entre contadores e vale confirmação
       explícita.
    4. Se o cardápio passar a incluir bebidas industrializadas compradas
       prontas (refrigerante, cerveja, água mineral), esses itens NÃO
       devem usar esta mesma classificação — eles são revenda de
       terceiros (CFOP 5102) e costumam estar sujeitos a ICMS-ST
       (CSOSN 201/202/500 + CEST obrigatório). Veja ITENS_EXEMPLO abaixo
       para o padrão correto desses casos.

Idempotente: usa get_or_create por SKU, então rodar de novo não duplica
itens. Para os campos fiscais, só ATUALIZA quem ainda está com NCM vazio
(pendente) — não sobrescreve nada que o contador já tenha ajustado
manualmente no admin/API depois da primeira carga.

Uso: python manage.py seed_menu
"""
from django.core.management.base import BaseCommand

from apps.menu.models import MenuCategory, MenuItem

CATEGORIAS = [
    ('Entradas', 5),
    ('Na Brasa', 12),
    ('Guarnições', 20),
    ('Parrilla', 10),
    ('Bebidas sem álcool', 30), ('Cervejas', 40), ('Vinhos', 50), ('Cafés e Doces', 60),
]

# Itens de demonstração — (categoria, nome, setor, preço, sku, gtin, ncm, cest, cfop, csosn, un)
ITENS_EXEMPLO = [
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

# NCM/CFOP/CSOSN padrão para "produção própria" (prato preparado no local).
# Ver ressalvas no docstring do módulo antes de usar em produção.
NCM_PRODUCAO_PROPRIA = '21069090'   # 2106.90.90 — outras preparações alimentícias
CFOP_PRODUCAO_PROPRIA = '5101'      # venda de produção do estabelecimento
CSOSN_PADRAO = '102'                # tributação normal do ICMS, sem crédito, sem ST
ORIGEM_NACIONAL = '0'               # produção própria = não é revenda de mercadoria importada
PIS_COFINS_CST_PADRAO = '49'        # outras operações de saída (Simples Nacional / DAS único)

# Acompanhamento padrão dos pratos "na brasa" — Filé Mignon e Salmão têm
# acompanhamento próprio (ver cardápio impresso).
_ACOMP_PADRAO = 'Acompanha arroz, feijão, batata frita, molho à campanha, farofa e banana frita.'
_ACOMP_FILE_MIGNON = ('Acompanha arroz a piamontese ou branco, feijão, batata noisette, '
                       'molho à campanha, farofa e banana frita.')
_ACOMP_SALMAO = 'Acompanha arroz a piamontese ou branco, batata noisette e molho de alcaparras.'

# Cardápio real — (categoria, nome, setor, preço, sku, descrição/porção, unidade).
# Destino de impressão pelo SETOR: PARRILLA -> impressora da parrilla + painel
# da cozinha; COZINHA -> impressora + painel da cozinha; BAR -> só impressora.
CARDAPIO = [
    # Entradas -> impressora + cozinha
    ('Entradas', 'Pastel (8 unid)', 'COZINHA', '50.00', 'ENT-01',
     '8 unid — sabores: queijo cremoso, carne seca, costela e cupim (todos com catupiry)', 'UN'),
    ('Entradas', 'Batata Frita', 'COZINHA', '35.00', 'ENT-02', 'porção', 'PT'),
    ('Entradas', 'Pão de Alho c/ Linguiça', 'COZINHA', '45.00', 'ENT-03', '2 pães + 4 linguiças', 'UN'),
    ('Entradas', 'Pão de Alho (unid)', 'COZINHA', '7.00', 'ENT-04', 'unid', 'UN'),
    ('Entradas', 'Linguiça Aperitivo (4 unid)', 'COZINHA', '42.00', 'ENT-05',
     '4 unid — com molho à campanha e farofa', 'UN'),
    ('Entradas', 'Salada de Palmito', 'COZINHA', '60.00', 'ENT-06',
     'palmito, alface, rúcula, tomate e cebola roxa', 'PT'),

    # Pratos principais "Na Brasa" -> parrilla + painel da cozinha
    ('Na Brasa', 'Picanha 2kg', 'PARRILLA', '430.00', 'BRA-01', f'2kg - 4 pessoas. {_ACOMP_PADRAO}', 'UN'),
    ('Na Brasa', 'Picanha 1kg', 'PARRILLA', '265.00', 'BRA-02', f'1kg - 2 pessoas. {_ACOMP_PADRAO}', 'UN'),
    ('Na Brasa', 'Churrasco Misto - Picanha', 'PARRILLA', '290.00', 'BRA-03',
     f'1kg - 2 pessoas (filé de coxa, linguiça e picanha). {_ACOMP_PADRAO}', 'UN'),
    ('Na Brasa', 'Churrasco Misto - Chorizo', 'PARRILLA', '275.00', 'BRA-04',
     f'1kg - 2 pessoas (filé de coxa, linguiça e chorizo). {_ACOMP_PADRAO}', 'UN'),
    ('Na Brasa', 'Parrilla do Assador (picanha, ancho e chorizo)', 'PARRILLA', '360.00', 'BRA-05',
     f'1,4kg - 2 pessoas. {_ACOMP_PADRAO}', 'UN'),
    ('Na Brasa', 'Bife de Chorizo', 'PARRILLA', '250.00', 'BRA-06', f'1kg - 2 pessoas. {_ACOMP_PADRAO}', 'UN'),
    ('Na Brasa', 'Filé Mignon', 'PARRILLA', '270.00', 'BRA-07', f'1kg - 2 pessoas. {_ACOMP_FILE_MIGNON}', 'UN'),
    ('Na Brasa', 'Bife de Chorizo c/ Crosta de Alho', 'PARRILLA', '265.00', 'BRA-08',
     f'1kg - 2 pessoas. {_ACOMP_PADRAO}', 'UN'),
    ('Na Brasa', 'Bife Ancho', 'PARRILLA', '260.00', 'BRA-09', f'1kg - 2 pessoas. {_ACOMP_PADRAO}', 'UN'),
    ('Na Brasa', 'Bife Ancho c/ Crosta de Gorgonzola', 'PARRILLA', '280.00', 'BRA-10',
     f'1kg - 2 pessoas. {_ACOMP_PADRAO}', 'UN'),
    ('Na Brasa', "T'Bone", 'PARRILLA', '260.00', 'BRA-11',
     f"1kg - 2 pessoas (filé mignon + contrafilé). {_ACOMP_PADRAO}", 'UN'),
    ('Na Brasa', 'Short Rib', 'PARRILLA', '240.00', 'BRA-12', f'1kg - 2 pessoas. {_ACOMP_PADRAO}', 'UN'),
    ('Na Brasa', 'Filé de Coxa do Assador', 'PARRILLA', '180.00', 'BRA-13',
     f'1kg - 2 pessoas (frango). {_ACOMP_PADRAO}', 'UN'),
    ('Na Brasa', 'Salmão na Brasa c/ Molho de Alcaparras', 'PARRILLA', '250.00', 'BRA-14',
     f'1kg - 2 pessoas. {_ACOMP_SALMAO}', 'UN'),

    # Guarnições / acompanhamentos -> impressora + cozinha
    ('Guarnições', 'Batata Frita', 'COZINHA', '35.00', 'GUA-01', 'porção', 'PT'),
    ('Guarnições', 'Batata Noisette', 'COZINHA', '35.00', 'GUA-02', 'porção', 'PT'),
    ('Guarnições', 'Farofa de Ovo', 'COZINHA', '28.00', 'GUA-03', 'porção', 'PT'),
    ('Guarnições', 'Farofa Tradicional', 'COZINHA', '12.00', 'GUA-04', 'porção', 'PT'),
    ('Guarnições', 'Arroz', 'COZINHA', '22.00', 'GUA-05', 'porção', 'PT'),
    ('Guarnições', 'Arroz à Piamontese', 'COZINHA', '32.00', 'GUA-06', 'porção', 'PT'),
    ('Guarnições', 'Feijão', 'COZINHA', '12.00', 'GUA-07', 'porção', 'PT'),
    ('Guarnições', 'Maionese', 'COZINHA', '18.00', 'GUA-08', 'porção', 'PT'),
    ('Guarnições', 'Molho à Campanha', 'COZINHA', '12.00', 'GUA-09', 'porção', 'PT'),
    ('Guarnições', 'Ovo Frito (02 unid)', 'COZINHA', '12.00', 'GUA-10', '2 unid', 'UN'),
    ('Guarnições', 'Banana Frita', 'COZINHA', '12.00', 'GUA-11', 'porção', 'PT'),
    ('Guarnições', 'Farofa de Bacon Crocante c/ Panko', 'COZINHA', '20.00', 'GUA-12', 'porção', 'PT'),
]


class Command(BaseCommand):
    help = 'Popula o cardápio (exemplos + cardápio real, com classificação fiscal padrão). Idempotente.'

    def handle(self, *args, **options):
        cats = {}
        for nome, ordem in CATEGORIAS:
            cat, _ = MenuCategory.objects.get_or_create(name=nome, defaults={'display_order': ordem})
            cats[nome] = cat
        self.stdout.write(self.style.SUCCESS(f'{len(cats)} categorias.'))

        criados = 0
        for (cat, nome, setor, preco, sku, gtin, ncm, cest, cfop, csosn, un) in ITENS_EXEMPLO:
            _, created = MenuItem.objects.get_or_create(sku=sku, defaults=dict(
                category=cats[cat], name=nome, sector=setor, price=preco,
                barcode_gtin=gtin, ncm=ncm, cest=cest, cfop=cfop, csosn=csosn,
                unit_commercial=un, unit_taxable=un, origem='0',
                pis_cst='49', cofins_cst='49',
            ))
            criados += int(created)

        preenchidos = 0
        for (cat, nome, setor, preco, sku, descricao, un) in CARDAPIO:
            defaults = dict(
                category=cats[cat], name=nome, sector=setor, price=preco,
                description=descricao,
                ncm=NCM_PRODUCAO_PROPRIA, cest='', cfop=CFOP_PRODUCAO_PROPRIA, csosn=CSOSN_PADRAO,
                unit_commercial=un, unit_taxable=un, origem=ORIGEM_NACIONAL,
                pis_cst=PIS_COFINS_CST_PADRAO, pis_aliquota='0',
                cofins_cst=PIS_COFINS_CST_PADRAO, cofins_aliquota='0',
            )
            obj, created = MenuItem.objects.get_or_create(sku=sku, defaults=defaults)
            criados += int(created)

            # A descrição é conteúdo do cardápio (não fiscal) — mantém sempre
            # sincronizada com o texto acima, mesmo em itens já existentes.
            if not created and obj.description != descricao:
                obj.description = descricao
                obj.save(update_fields=['description'])

            # Não sobrescreve fiscal já ajustado manualmente — só preenche
            # pendências (item criado antes desta versão do seed, com NCM
            # ainda vazio).
            if not created and not obj.ncm:
                obj.ncm = NCM_PRODUCAO_PROPRIA
                obj.cfop = CFOP_PRODUCAO_PROPRIA
                obj.csosn = CSOSN_PADRAO
                obj.origem = ORIGEM_NACIONAL
                obj.pis_cst = PIS_COFINS_CST_PADRAO
                obj.cofins_cst = PIS_COFINS_CST_PADRAO
                obj.save(update_fields=[
                    'ncm', 'cfop', 'csosn', 'origem', 'pis_cst', 'cofins_cst',
                ])
                preenchidos += 1

        self.stdout.write(self.style.SUCCESS(
            f'{criados} itens novos ({MenuItem.objects.count()} no total).'))
        if preenchidos:
            self.stdout.write(self.style.SUCCESS(
                f'{preenchidos} itens do cardápio real tiveram a classificação '
                f'fiscal padrão preenchida (NCM 2106.90.90 / CFOP 5101 / CSOSN 102). '
                f'Confirme com o contador antes de emitir NFC-e real — '
                f'veja o docstring deste arquivo.'))
