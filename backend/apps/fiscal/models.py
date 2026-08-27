"""
Configuração fiscal do emitente e documentos NFC-e gerados.
"""
from django.core.exceptions import ValidationError
from django.db import models


class Environment(models.TextChoices):
    HOMOLOGACAO = '2', 'Homologação'
    PRODUCAO = '1', 'Produção'


class FiscalSettings(models.Model):
    """Dados do emitente + credenciais da NFC-e. Registro único (pk=1)."""
    razao_social = models.CharField('Razão social', max_length=200, blank=True)
    nome_fantasia = models.CharField('Nome fantasia', max_length=200, blank=True)
    cnpj = models.CharField('CNPJ', max_length=14, blank=True)
    inscricao_estadual = models.CharField('Inscrição estadual', max_length=20, blank=True)
    regime_tributario = models.CharField('Regime (CRT)', max_length=1, default='1',
                                         help_text='1 = Simples Nacional')

    uf = models.CharField('UF', max_length=2, blank=True)
    municipio_ibge = models.CharField('Código IBGE do município', max_length=7, blank=True)
    municipio_nome = models.CharField('Município', max_length=120, blank=True)
    logradouro = models.CharField('Logradouro', max_length=160, blank=True)
    numero = models.CharField('Número', max_length=20, blank=True)
    bairro = models.CharField('Bairro', max_length=80, blank=True)
    cep = models.CharField('CEP', max_length=8, blank=True)
    fone = models.CharField('Telefone', max_length=14, blank=True)

    environment = models.CharField('Ambiente', max_length=1, choices=Environment.choices,
                                   default=Environment.HOMOLOGACAO)
    serie_nfce = models.PositiveIntegerField('Série da NFC-e', default=1)
    proximo_numero = models.PositiveIntegerField('Próximo número', default=1)

    # Credenciais do QR Code (Portal SEFAZ da UF)
    csc_id = models.CharField('ID do CSC (idToken)', max_length=6, blank=True)
    csc_token = models.CharField('CSC (token)', max_length=64, blank=True)

    # Certificado A1 (.pfx / .p12) para assinatura e mTLS com a SEFAZ
    certificado_path = models.CharField('Caminho do certificado A1', max_length=255, blank=True)
    certificado_senha = models.CharField('Senha do certificado', max_length=128, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuração Fiscal'
        verbose_name_plural = 'Configuração Fiscal'

    def __str__(self):
        return f'Config. Fiscal ({self.get_environment_display()})'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def missing_for_transmission(self):
        """Lista o que ainda falta para transmitir à SEFAZ (homologação)."""
        campos = {
            'cnpj': self.cnpj, 'inscricao_estadual': self.inscricao_estadual,
            'uf': self.uf, 'municipio_ibge': self.municipio_ibge,
            'razao_social': self.razao_social, 'csc_id': self.csc_id,
            'csc_token': self.csc_token, 'certificado_path': self.certificado_path,
            'certificado_senha': self.certificado_senha,
        }
        return [nome for nome, valor in campos.items() if not valor]

    @property
    def pronto_para_transmitir(self):
        return not self.missing_for_transmission()


class InvoiceStatus(models.TextChoices):
    RASCUNHO = 'RASCUNHO', 'Rascunho'
    ASSINADA = 'ASSINADA', 'Assinada'
    AUTORIZADA = 'AUTORIZADA', 'Autorizada'
    REJEITADA = 'REJEITADA', 'Rejeitada'
    CANCELADA = 'CANCELADA', 'Cancelada'
    NAO_CONFIGURADO = 'NAO_CONFIGURADO', 'Não configurado'


class Invoice(models.Model):
    """NFC-e (modelo 65) gerada a partir de um pedido."""
    order = models.ForeignKey('orders.Order', on_delete=models.PROTECT, related_name='invoices',
                              verbose_name='Pedido')
    numero = models.PositiveIntegerField('Número', null=True, blank=True)
    serie = models.PositiveIntegerField('Série', null=True, blank=True)
    codigo_numerico = models.CharField('Código numérico (cNF)', max_length=8, blank=True)
    chave_acesso = models.CharField('Chave de acesso', max_length=44, blank=True, db_index=True)
    ambiente = models.CharField('Ambiente', max_length=1, choices=Environment.choices,
                                default=Environment.HOMOLOGACAO)

    status = models.CharField('Status', max_length=16, choices=InvoiceStatus.choices,
                              default=InvoiceStatus.RASCUNHO)
    valor_total = models.DecimalField('Valor total', max_digits=12, decimal_places=2, default=0)

    xml = models.TextField('XML', blank=True)
    xml_assinado = models.TextField('XML assinado', blank=True)
    protocolo_autorizacao = models.CharField('Protocolo', max_length=20, blank=True)
    qr_code_data = models.TextField('QR Code (URL)', blank=True)
    url_consulta = models.URLField('URL de consulta', blank=True)
    motivo = models.CharField('Mensagem SEFAZ / motivo', max_length=255, blank=True)

    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='invoices')
    created_at = models.DateTimeField(auto_now_add=True)
    autorizada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'NFC-e'
        verbose_name_plural = 'NFC-e'
        ordering = ['-created_at']

    def __str__(self):
        return f'NFC-e {self.numero or "s/n"} — {self.get_status_display()}'
