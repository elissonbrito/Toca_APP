"""
Cliente SEFAZ para NFC-e (assinatura + transmissão).

O código deterministico (montar XML, chave de acesso, QR Code) roda sempre.
A assinatura digital e a transmissão exigem:
  - certificado A1 (.pfx) válido + senha  -> settings.certificado_path / _senha
  - bibliotecas 'cryptography' e 'signxml' instaladas
  - endpoint da SEFAZ da UF (webservice NFeAutorizacao4)

Sem esses requisitos, as operações retornam SefazNaoConfigurado com o
checklist do que falta — nunca um "sucesso" simulado.
"""
from dataclasses import dataclass, field


class SefazError(Exception):
    pass


class SefazNaoConfigurado(SefazError):
    def __init__(self, faltando):
        self.faltando = list(faltando)
        super().__init__('Transmissão à SEFAZ não configurada: ' + ', '.join(self.faltando))


@dataclass
class TransmissionResult:
    autorizada: bool
    status: str
    mensagem: str
    protocolo: str = ''
    xml_retorno: str = ''
    faltando: list = field(default_factory=list)


def _check_deps():
    faltando = []
    try:
        import cryptography  # noqa: F401
    except ImportError:
        faltando.append("biblioteca 'cryptography'")
    try:
        import signxml  # noqa: F401
    except ImportError:
        faltando.append("biblioteca 'signxml'")
    return faltando


def sign_xml(xml: str, settings) -> str:
    """Assina o XML da NFC-e (XMLDSig, enveloped). Lança SefazNaoConfigurado."""
    faltando = _check_deps()
    if not settings.certificado_path:
        faltando.append('certificado A1 (certificado_path)')
    if not settings.certificado_senha:
        faltando.append('senha do certificado')
    if faltando:
        raise SefazNaoConfigurado(faltando)

    # Caminho real (ativado quando as dependências e o certificado existem):
    from cryptography.hazmat.primitives.serialization import pkcs12
    from lxml import etree
    from signxml import XMLSigner, methods

    with open(settings.certificado_path, 'rb') as fh:
        key, cert, _ = pkcs12.load_key_and_certificates(
            fh.read(), settings.certificado_senha.encode()
        )
    root = etree.fromstring(xml.encode())
    inf = root.find('.//{http://www.portalfiscal.inf.br/nfe}infNFe')
    signed = XMLSigner(
        method=methods.enveloped, signature_algorithm='rsa-sha1',
        digest_algorithm='sha1', c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315',
    ).sign(root, key=key, cert=cert, reference_uri='#' + inf.get('Id'))
    return etree.tostring(signed, encoding='unicode')


def transmitir(xml_assinado: str, settings) -> TransmissionResult:
    """Envia o XML assinado ao webservice NFeAutorizacao4 da SEFAZ da UF."""
    faltando = settings.missing_for_transmission() + _check_deps()
    if faltando:
        return TransmissionResult(
            autorizada=False, status='NAO_CONFIGURADO',
            mensagem='Falta configurar a integração com a SEFAZ.', faltando=faltando,
        )

    try:
        import requests
        from requests_pkcs12 import Pkcs12Adapter
    except ImportError:
        return TransmissionResult(
            autorizada=False, status='NAO_CONFIGURADO',
            mensagem="Instale 'requests-pkcs12' para a transmissão mTLS.",
            faltando=["biblioteca 'requests-pkcs12'"],
        )

    endpoint = _endpoint_autorizacao(settings.uf, settings.environment)
    if not endpoint:
        return TransmissionResult(
            autorizada=False, status='NAO_CONFIGURADO',
            mensagem=f'Endpoint NFeAutorizacao4 não cadastrado para a UF {settings.uf}.',
            faltando=[f'endpoint SEFAZ da UF {settings.uf}'],
        )

    session = requests.Session()
    session.mount(endpoint, Pkcs12Adapter(
        pkcs12_filename=settings.certificado_path,
        pkcs12_password=settings.certificado_senha,
    ))
    envelope = _soap_envelope(xml_assinado)
    resp = session.post(endpoint, data=envelope.encode('utf-8'), headers={
        'Content-Type': 'application/soap+xml; charset=utf-8',
    }, timeout=30)
    resp.raise_for_status()
    return _parse_retorno(resp.text)


def _endpoint_autorizacao(uf: str, ambiente: str) -> str:
    # Cadastre aqui os webservices reais da sua UF (homologação/produção).
    return ''


def _soap_envelope(xml_assinado: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">'
        '<soap12:Body>'
        '<nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4">'
        f'<enviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
        '<idLote>1</idLote><indSinc>1</indSinc>'
        f'{xml_assinado}</enviNFe>'
        '</nfeDadosMsg></soap12:Body></soap12:Envelope>'
    )


def _parse_retorno(texto: str) -> TransmissionResult:
    import re
    cstat = (re.search(r'<cStat>(\d+)</cStat>', texto) or [None, ''])[1]
    xmotivo = (re.search(r'<xMotivo>(.*?)</xMotivo>', texto) or [None, ''])[1]
    nprot = (re.search(r'<nProt>(\d+)</nProt>', texto) or [None, ''])[1]
    autorizada = cstat in ('100', '150')
    return TransmissionResult(
        autorizada=autorizada,
        status='AUTORIZADA' if autorizada else 'REJEITADA',
        mensagem=f'{cstat} - {xmotivo}', protocolo=nprot, xml_retorno=texto,
    )
