"""
Chave de acesso da NFC-e (44 dígitos) e dígito verificador (módulo 11).

Layout (NT 2015/002, modelo 65):
  cUF(2) AAMM(4) CNPJ(14) mod(2) serie(3) nNF(9) tpEmis(1) cNF(8) cDV(1)
"""
from datetime import date

UF_IBGE = {
    'AC': '12', 'AL': '27', 'AP': '16', 'AM': '13', 'BA': '29', 'CE': '23',
    'DF': '53', 'ES': '32', 'GO': '52', 'MA': '21', 'MT': '51', 'MS': '50',
    'MG': '31', 'PA': '15', 'PB': '25', 'PR': '41', 'PE': '26', 'PI': '22',
    'RJ': '33', 'RN': '24', 'RS': '43', 'RO': '11', 'RR': '14', 'SC': '42',
    'SP': '35', 'SE': '28', 'TO': '17',
}


def dv_modulo11(key43: str) -> str:
    """DV módulo 11 (pesos 2..9 cíclicos, da direita para a esquerda)."""
    if len(key43) != 43 or not key43.isdigit():
        raise ValueError('A base da chave deve ter 43 dígitos numéricos.')
    weights = [2, 3, 4, 5, 6, 7, 8, 9]
    total = 0
    for i, ch in enumerate(reversed(key43)):
        total += int(ch) * weights[i % 8]
    rem = total % 11
    dv = 11 - rem
    return '0' if dv in (0, 1, 10, 11) else str(dv)


def build_access_key(*, uf: str, cnpj: str, modelo: str = '65', serie: int,
                     numero: int, tp_emis: int = 1, codigo_numerico: int,
                     competencia: date | None = None) -> str:
    competencia = competencia or date.today()
    cuf = UF_IBGE[uf.upper()]
    aamm = competencia.strftime('%y%m')
    cnpj_d = ''.join(filter(str.isdigit, cnpj)).zfill(14)
    base = (
        f'{cuf}{aamm}{cnpj_d}{modelo}'
        f'{int(serie):03d}{int(numero):09d}{int(tp_emis)}'
        f'{int(codigo_numerico):08d}'
    )
    return base + dv_modulo11(base)


def format_access_key(key44: str) -> str:
    return ' '.join(key44[i:i + 4] for i in range(0, 44, 4))
