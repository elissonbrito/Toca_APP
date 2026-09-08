"""
Printing app - impressoras térmicas, configuração geral e fila de impressão.

O envio físico é feito pelo navegador via QZ Tray (ESC/POS). O backend só
gerencia o cadastro de impressoras, a configuração de layout e a fila (FIFO,
por ordem de emissão).
"""
from django.db import models


class PrinterSector(models.TextChoices):
    COZINHA = 'COZINHA', 'Cozinha'
    PARRILLA = 'PARRILLA', 'Parrilla'
    BAR = 'BAR', 'Bar / Bebidas'
    CAIXA = 'CAIXA', 'Caixa / Recibo'


class Printer(models.Model):
    name = models.CharField('Nome', max_length=120)
    sector = models.CharField('Setor', max_length=10, choices=PrinterSector.choices)
    qz_printer_name = models.CharField(
        'Impressora no QZ Tray', max_length=200,
        help_text='Exatamente como o nome aparece no sistema operacional / QZ Tray.',
    )
    is_active = models.BooleanField('Ativa', default=True)
    copies = models.PositiveSmallIntegerField('Vias', default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Impressora'
        verbose_name_plural = 'Impressoras'
        ordering = ['sector', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_sector_display()})'


class PrintSettings(models.Model):
    """Configuração geral de impressão — singleton (pk=1)."""
    header_title = models.CharField('Título do cabeçalho', max_length=120, default='Toca do Espanhol')
    header_image = models.TextField('Logo / imagem (data URL base64)', blank=True)
    watermark_text = models.CharField("Marca d'água", max_length=80, blank=True)
    footer_text = models.CharField('Rodapé', max_length=200, blank=True)

    font_family = models.CharField(
        'Fonte', max_length=1, default='A',
        choices=[('A', 'Padrão (A)'), ('B', 'Condensada (B)')],
    )
    font_size = models.PositiveSmallIntegerField('Tamanho (1 a 4)', default=1)
    bold = models.BooleanField('Negrito', default=True)
    align = models.CharField(
        'Alinhamento', max_length=6, default='left',
        choices=[('left', 'Esquerda'), ('center', 'Centro'), ('right', 'Direita')],
    )
    margin_left = models.PositiveSmallIntegerField('Margem esquerda (colunas)', default=0)
    margin_top = models.PositiveSmallIntegerField('Linhas em branco no topo', default=0)
    margin_bottom = models.PositiveSmallIntegerField('Linhas em branco no fim', default=3)
    paper_width = models.PositiveSmallIntegerField('Largura do papel (colunas)', default=48)
    cut_paper = models.BooleanField('Cortar papel ao final', default=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuração de impressão'
        verbose_name_plural = 'Configuração de impressão'

    def __str__(self):
        return 'Configuração de impressão'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class PrintJobStatus(models.TextChoices):
    PENDENTE = 'PENDENTE', 'Na fila'
    IMPRESSO = 'IMPRESSO', 'Impresso'
    ERRO = 'ERRO', 'Erro'
    CANCELADO = 'CANCELADO', 'Cancelado'


class PrintJob(models.Model):
    """Um trabalho de impressão (normalmente 1 item de comanda para 1 impressora)."""
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='print_jobs')
    order_item = models.ForeignKey(
        'orders.OrderItem', on_delete=models.CASCADE,
        related_name='print_jobs', null=True, blank=True,
    )
    printer = models.ForeignKey(
        Printer, on_delete=models.SET_NULL, related_name='jobs', null=True, blank=True,
    )
    sector = models.CharField('Setor', max_length=10)
    title = models.CharField('Título', max_length=160, blank=True)
    body = models.TextField('Conteúdo (texto puro)')
    status = models.CharField(
        max_length=10, choices=PrintJobStatus.choices, default=PrintJobStatus.PENDENTE,
    )
    error_message = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    printed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Trabalho de impressão'
        verbose_name_plural = 'Fila de impressão'
        ordering = ['id']  # FIFO — ordem de emissão

    def __str__(self):
        return f'PrintJob #{self.id} {self.sector} ({self.status})'
