"""
Geração do XML da NFC-e (modelo 65, layout 4.00).

Observação: este builder produz um XML estruturalmente compatível com o layout
4.00 para conferência/assinatura. A validação final contra o XSD oficial e a
transmissão são responsabilidade do fluxo SEFAZ (apps/fiscal/sefaz.py).
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from xml.etree.ElementTree import Element, SubElement, tostring

NS = 'http://www.portalfiscal.inf.br/nfe'
VERSAO = '4.00'


def _money(value) -> str:
    return str(Decimal(str(value or 0)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def _qty(value) -> str:
    return str(Decimal(str(value or 0)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP))


def _text(parent, tag, value):
    el = SubElement(parent, tag)
    el.text = '' if value is None else str(value)
    return el


def _digits(value) -> str:
    return ''.join(ch for ch in str(value or '') if ch.isdigit())


def build_nfce_xml(invoice, order, settings) -> str:
    """Monta o XML <NFe> (sem assinatura) da NFC-e para o pedido."""
    items = list(order.items.exclude(status='CANCELADO'))

    nfe = Element('NFe', xmlns=NS)
    inf = SubElement(nfe, 'infNFe', versao=VERSAO, Id=f'NFe{invoice.chave_acesso}')

    # ── ide ────────────────────────────────────────────────────
    ide = SubElement(inf, 'ide')
    _text(ide, 'cUF', invoice.chave_acesso[:2])
    _text(ide, 'cNF', invoice.codigo_numerico)
    _text(ide, 'natOp', 'Venda de mercadoria')
    _text(ide, 'mod', '65')
    _text(ide, 'serie', invoice.serie)
    _text(ide, 'nNF', invoice.numero)
    _text(ide, 'dhEmi', invoice.created_at.strftime('%Y-%m-%dT%H:%M:%S%z') or '')
    _text(ide, 'tpNF', '1')            # saída
    _text(ide, 'idDest', '1')          # operação interna
    _text(ide, 'cMunFG', settings.municipio_ibge)
    _text(ide, 'tpImp', '4')           # DANFE NFC-e
    _text(ide, 'tpEmis', '1')          # normal
    _text(ide, 'cDV', invoice.chave_acesso[-1])
    _text(ide, 'tpAmb', invoice.ambiente)
    _text(ide, 'finNFe', '1')
    _text(ide, 'indFinal', '1')        # consumidor final
    _text(ide, 'indPres', '1')         # presencial
    _text(ide, 'procEmi', '0')
    _text(ide, 'verProc', 'toca-do-espanhol/1.0')

    # ── emit ───────────────────────────────────────────────────
    emit = SubElement(inf, 'emit')
    _text(emit, 'CNPJ', _digits(settings.cnpj))
    _text(emit, 'xNome', settings.razao_social)
    if settings.nome_fantasia:
        _text(emit, 'xFant', settings.nome_fantasia)
    ender = SubElement(emit, 'enderEmit')
    _text(ender, 'xLgr', settings.logradouro or 'S/N')
    _text(ender, 'nro', settings.numero or 'S/N')
    _text(ender, 'xBairro', settings.bairro or 'CENTRO')
    _text(ender, 'cMun', settings.municipio_ibge)
    _text(ender, 'xMun', settings.municipio_nome)
    _text(ender, 'UF', settings.uf)
    _text(ender, 'CEP', _digits(settings.cep))
    _text(emit, 'IE', _digits(settings.inscricao_estadual))
    _text(emit, 'CRT', settings.regime_tributario)  # 1 = Simples Nacional

    # ── det (itens) ────────────────────────────────────────────
    total_prod = Decimal('0')
    for i, it in enumerate(items, start=1):
        det = SubElement(inf, 'det', nItem=str(i))
        prod = SubElement(det, 'prod')
        _text(prod, 'cProd', it.menu_item.sku if it.menu_item_id else f'LIVRE{it.id}')
        _text(prod, 'cEAN', (it.menu_item.barcode_gtin or 'SEM GTIN') if it.menu_item_id else 'SEM GTIN')
        _text(prod, 'xProd', it.product_name)
        _text(prod, 'NCM', it.fiscal_ncm or '00000000')
        if it.fiscal_cest:
            _text(prod, 'CEST', it.fiscal_cest)
        _text(prod, 'CFOP', it.fiscal_cfop or '5102')
        _text(prod, 'uCom', it.fiscal_unit or 'UN')
        _text(prod, 'qCom', _qty(it.quantity))
        _text(prod, 'vUnCom', _money(it.unit_price))
        _text(prod, 'vProd', _money(it.total_price))
        _text(prod, 'cEANTrib', (it.menu_item.barcode_gtin or 'SEM GTIN') if it.menu_item_id else 'SEM GTIN')
        _text(prod, 'uTrib', it.fiscal_unit or 'UN')
        _text(prod, 'qTrib', _qty(it.quantity))
        _text(prod, 'vUnTrib', _money(it.unit_price))
        _text(prod, 'indTot', '1')
        total_prod += Decimal(str(it.total_price or 0))

        imposto = SubElement(det, 'imposto')
        icms = SubElement(imposto, 'ICMS')
        csosn = it.fiscal_csosn or '102'
        grp = SubElement(icms, f'ICMSSN{ "500" if csosn == "500" else "102" }')
        _text(grp, 'orig', it.fiscal_origem or '0')
        _text(grp, 'CSOSN', csosn)
        # PIS/COFINS — Simples Nacional: normalmente "outras operações"
        pis = SubElement(imposto, 'PIS')
        pisout = SubElement(pis, 'PISOutr')
        _text(pisout, 'CST', '49')
        _text(pisout, 'vBC', '0.00')
        _text(pisout, 'pPIS', '0.00')
        _text(pisout, 'vPIS', '0.00')
        cof = SubElement(imposto, 'COFINS')
        cofout = SubElement(cof, 'COFINSOutr')
        _text(cofout, 'CST', '49')
        _text(cofout, 'vBC', '0.00')
        _text(cofout, 'pCOFINS', '0.00')
        _text(cofout, 'vCOFINS', '0.00')

    # ── total ──────────────────────────────────────────────────
    total = SubElement(inf, 'total')
    icmstot = SubElement(total, 'ICMSTot')
    for tag in ('vBC', 'vICMS', 'vICMSDeson', 'vFCP', 'vBCST', 'vST', 'vFCPST',
                'vFCPSTRet', 'vProd'):
        _text(icmstot, tag, _money(total_prod if tag == 'vProd' else 0))
    for tag in ('vFrete', 'vSeg', 'vDesc', 'vII', 'vIPI', 'vIPIDevol', 'vPIS', 'vCOFINS', 'vOutro'):
        _text(icmstot, tag, '0.00')
    _text(icmstot, 'vNF', _money(total_prod))

    # ── transp / pag ──────────────────────────────────────────
    transp = SubElement(inf, 'transp')
    _text(transp, 'modFrete', '9')  # sem frete

    pag = SubElement(inf, 'pag')
    for p in order.payments.all() or [None]:
        detpag = SubElement(pag, 'detPag')
        _text(detpag, 'tPag', _map_tpag(getattr(p, 'payment_method', None)))
        _text(detpag, 'vPag', _money(getattr(p, 'amount', total_prod)))

    info = SubElement(inf, 'infAdic')
    _text(info, 'infCpl', f'Pedido #{order.id} - Mesa {order.table.number} - Toca do Espanhol')

    return tostring(nfe, encoding='unicode')


def _map_tpag(method) -> str:
    return {
        'DINHEIRO': '01',
        'CREDITO': '03',
        'DEBITO': '04',
        'PIX': '17',
    }.get(method, '99')
