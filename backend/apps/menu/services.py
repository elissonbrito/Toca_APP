"""
Conferência fiscal do cardápio.

Regras de acordo com as exigências de NFC-e (Simples Nacional):
- NCM obrigatório e com 8 dígitos.
- CFOP obrigatório, saída (5/6/7).
- CSOSN obrigatório.
- Origem obrigatória.
- CEST obrigatório quando o CSOSN indica ICMS-ST.
- CSOSN 101/201/900 exigem alíquota de ICMS próprio informada.
- CST de PIS e COFINS obrigatórios.
- GTIN, se informado, precisa ter dígito verificador válido.
"""
from . import fiscal
from .fiscal import gtin_is_valid


class FiscalConferenceService:
    @staticmethod
    def check_item(item):
        errors = []
        warnings = []

        ncm = fiscal._digits(item.ncm)
        if not ncm:
            errors.append('NCM não informado.')
        elif len(ncm) != 8:
            errors.append('NCM deve ter 8 dígitos.')

        if not item.cfop:
            errors.append('CFOP não informado.')

        if not item.csosn:
            errors.append('CSOSN não informado.')

        if not item.origem:
            errors.append('Origem da mercadoria não informada.')

        if item.csosn in fiscal.CSOSN_COM_ST and not fiscal._digits(item.cest):
            errors.append(f'CSOSN {item.csosn} indica ICMS-ST: CEST é obrigatório.')

        if item.csosn in fiscal.CSOSN_COM_ICMS_PROPRIO and item.icms_aliquota in (None, ''):
            errors.append(f'CSOSN {item.csosn} exige a alíquota de ICMS próprio.')

        if not item.pis_cst:
            errors.append('CST de PIS não informado.')
        if not item.cofins_cst:
            errors.append('CST de COFINS não informado.')

        if item.barcode_gtin and not gtin_is_valid(item.barcode_gtin):
            warnings.append('GTIN informado tem dígito verificador inválido.')

        if item.sector == 'BAR' and not fiscal._digits(item.cest):
            warnings.append('Item de bar/bebida geralmente está sujeito a ICMS-ST — confirme se precisa de CEST.')

        if item.price is None or item.price <= 0:
            warnings.append('Preço de venda zerado ou negativo.')

        if not item.is_active:
            warnings.append('Item inativo — não entra no cardápio nem na conferência de venda.')

        return {
            'item_id': item.id,
            'sku': item.sku,
            'name': item.name,
            'ok': not errors,
            'errors': errors,
            'warnings': warnings,
        }

    @staticmethod
    def check_catalog(queryset):
        results = [FiscalConferenceService.check_item(i) for i in queryset]
        with_errors = [r for r in results if r['errors']]
        with_warnings = [r for r in results if r['warnings'] and not r['errors']]
        return {
            'total': len(results),
            'conformes': len(results) - len(with_errors),
            'com_pendencias': len(with_errors),
            'com_alertas': len(with_warnings),
            'pendencias': with_errors,
            'alertas': with_warnings,
        }
