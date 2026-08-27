"""
Constantes e validadores fiscais para o cadastro do cardápio (Simples Nacional).

Referências:
- NCM: Nomenclatura Comum do Mercosul (8 dígitos) — obrigatório na NF-e/NFC-e.
- CEST: Código Especificador da Substituição Tributária (7 dígitos) — obrigatório
  quando a mercadoria está sujeita a ICMS-ST (comum em bebidas).
- CFOP: Código Fiscal de Operações e Prestações (4 dígitos).
- CSOSN: Código de Situação da Operação no Simples Nacional (3 dígitos).
- Origem: origem da mercadoria (0 a 8) — 1º dígito do CST/CSOSN.
- CST PIS/COFINS: tabelas da EFD-Contribuições.
- GTIN (EAN-8/12/13/14): dígito verificador módulo 10.
"""
import re

from django.core.exceptions import ValidationError
from django.db import models


class Origem(models.TextChoices):
    N_0 = '0', '0 - Nacional (exceto 3, 4, 5 e 8)'
    N_1 = '1', '1 - Estrangeira - importação direta (exceto 6)'
    N_2 = '2', '2 - Estrangeira - adquirida no mercado interno (exceto 7)'
    N_3 = '3', '3 - Nacional, conteúdo de importação > 40% e <= 70%'
    N_4 = '4', '4 - Nacional, produção conforme processos produtivos básicos'
    N_5 = '5', '5 - Nacional, conteúdo de importação <= 40%'
    N_6 = '6', '6 - Estrangeira - importação direta, sem similar nacional (lista CAMEX)'
    N_7 = '7', '7 - Estrangeira - mercado interno, sem similar nacional (lista CAMEX)'
    N_8 = '8', '8 - Nacional, conteúdo de importação > 70%'


class CSOSN(models.TextChoices):
    C101 = '101', '101 - Tributada pelo Simples Nacional com permissão de crédito'
    C102 = '102', '102 - Tributada pelo Simples Nacional sem permissão de crédito'
    C103 = '103', '103 - Isenção do ICMS no Simples Nacional para faixa de receita bruta'
    C201 = '201', '201 - Simples Nacional com permissão de crédito e cobrança de ICMS-ST'
    C202 = '202', '202 - Simples Nacional sem permissão de crédito e com cobrança de ICMS-ST'
    C203 = '203', '203 - Isenção do ICMS no Simples Nacional e com cobrança de ICMS-ST'
    C300 = '300', '300 - Imune'
    C400 = '400', '400 - Não tributada pelo Simples Nacional'
    C500 = '500', '500 - ICMS cobrado anteriormente por ST ou por antecipação'
    C900 = '900', '900 - Outros'


# Exige informar alíquota/base de ICMS próprio no item.
CSOSN_COM_ICMS_PROPRIO = {'101', '201', '900'}
# Indica mercadoria sujeita a ICMS-ST -> CEST passa a ser obrigatório.
CSOSN_COM_ST = {'201', '202', '203', '500'}


class CST_PIS_COFINS(models.TextChoices):
    T01 = '01', '01 - Operação tributável com alíquota básica'
    T02 = '02', '02 - Operação tributável com alíquota diferenciada'
    T04 = '04', '04 - Operação tributável monofásica - revenda a alíquota zero'
    T06 = '06', '06 - Operação tributável a alíquota zero'
    T07 = '07', '07 - Operação isenta da contribuição'
    T08 = '08', '08 - Operação sem incidência da contribuição'
    T09 = '09', '09 - Operação com suspensão da contribuição'
    T49 = '49', '49 - Outras operações de saída'


class CFOP(models.TextChoices):
    F5101 = '5101', '5101 - Venda de produção do estabelecimento'
    F5102 = '5102', '5102 - Venda de mercadoria adquirida de terceiros'
    F5103 = '5103', '5103 - Venda de produção do estabelecimento (não contribuinte)'
    F5104 = '5104', '5104 - Venda de mercadoria de terceiros (não contribuinte)'
    F5405 = '5405', '5405 - Venda de mercadoria com ICMS-ST, na condição de substituído'
    F5656 = '5656', '5656 - Venda de combustível/lubrificante adquirido de terceiros'
    F5933 = '5933', '5933 - Prestação de serviço tributado pelo ISSQN'


class UnidadeMedida(models.TextChoices):
    UN = 'UN', 'Unidade'
    PC = 'PC', 'Peça'
    KG = 'KG', 'Quilograma'
    G = 'G', 'Grama'
    L = 'L', 'Litro'
    ML = 'ML', 'Mililitro'
    DZ = 'DZ', 'Dúzia'
    PT = 'PT', 'Porção'
    CX = 'CX', 'Caixa'
    GF = 'GF', 'Garrafa'


# NCMs comuns em restaurante/parrilla — sugestões para autocompletar.
NCM_SUGESTOES = [
    ('02013000', 'Carne bovina fresca ou refrigerada, desossada'),
    ('02023000', 'Carne bovina congelada, desossada'),
    ('02032900', 'Carne suína congelada'),
    ('02071400', 'Pedaços e miudezas de galos/galinhas, congelados'),
    ('03047900', 'Filés de peixe congelados'),
    ('16025000', 'Preparações de carne bovina'),
    ('19059090', 'Produtos de padaria/pastelaria (pães, focaccia)'),
    ('20059900', 'Outros produtos hortícolas preparados (guarnições)'),
    ('21039021', 'Preparações para molhos e molhos preparados (chimichurri)'),
    ('22011000', 'Águas minerais e gaseificadas'),
    ('22021000', 'Águas, incl. minerais/gaseificadas, adicionadas de açúcar (refrigerante)'),
    ('22029900', 'Outras bebidas não alcoólicas (sucos prontos)'),
    ('22030000', 'Cervejas de malte'),
    ('22042100', 'Vinhos de uvas frescas, em recipientes <= 2 litros'),
    ('22083000', 'Uísques'),
    ('22084000', 'Rum e outras aguardentes de cana'),
    ('09011110', 'Café não torrado, não descafeinado, em grão'),
    ('21011110', 'Café solúvel / extratos de café'),
]

_ONLY_DIGITS = re.compile(r'^\d+$')


def _digits(value):
    return re.sub(r'\D', '', value or '')


def validate_ncm(value):
    v = _digits(value)
    if len(v) != 8:
        raise ValidationError('NCM deve ter 8 dígitos numéricos.')


def validate_cest(value):
    if not value:
        return
    v = _digits(value)
    if len(v) != 7:
        raise ValidationError('CEST deve ter 7 dígitos numéricos.')


def validate_cfop(value):
    v = _digits(value)
    if len(v) != 4:
        raise ValidationError('CFOP deve ter 4 dígitos.')
    if v[0] not in {'5', '6', '7'}:
        raise ValidationError('CFOP de saída deve começar com 5 (interna), 6 (interestadual) ou 7 (exterior).')


def gtin_is_valid(value):
    """Valida o dígito verificador (módulo 10) de GTIN-8/12/13/14."""
    v = _digits(value)
    if len(v) not in (8, 12, 13, 14):
        return False
    *body, check = [int(d) for d in v]
    # Peso 3 e 1 alternados, a partir do dígito imediatamente à esquerda do DV.
    total = 0
    for i, digit in enumerate(reversed(body)):
        total += digit * (3 if i % 2 == 0 else 1)
    dv = (10 - (total % 10)) % 10
    return dv == check


def validate_gtin(value):
    if not value:
        return
    if not gtin_is_valid(value):
        raise ValidationError('GTIN/EAN inválido (dígito verificador não confere).')
