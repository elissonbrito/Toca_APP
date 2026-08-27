"""
Cardápio - categorias e itens com classificação fiscal (Simples Nacional).
"""
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify

from apps.orders.models import ItemSector
from . import fiscal

ZERO = Decimal('0')


class MenuCategory(models.Model):
    name = models.CharField('Nome', max_length=80, unique=True)
    slug = models.SlugField('Slug', max_length=90, unique=True, blank=True)
    display_order = models.PositiveIntegerField('Ordem', default=0)
    is_active = models.BooleanField('Ativa', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoria do Cardápio'
        verbose_name_plural = 'Categorias do Cardápio'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:90]
        super().save(*args, **kwargs)


class MenuItem(models.Model):
    """Item vendável do cardápio + sua classificação fiscal para NFC-e."""

    # ── Operacional ──────────────────────────────────────────────
    category = models.ForeignKey(
        MenuCategory, on_delete=models.PROTECT, related_name='items', verbose_name='Categoria'
    )
    name = models.CharField('Nome', max_length=150)
    description = models.TextField('Descrição', blank=True)
    sector = models.CharField('Setor de preparo', max_length=10, choices=ItemSector.choices,
                              default=ItemSector.COZINHA)
    price = models.DecimalField('Preço de venda', max_digits=10, decimal_places=2,
                                validators=[MinValueValidator(ZERO)])
    preparation_minutes = models.PositiveIntegerField('Tempo de preparo (min)', null=True, blank=True)
    is_active = models.BooleanField('Ativo', default=True)

    # ── Comercial ────────────────────────────────────────────────
    sku = models.CharField('Código interno (SKU)', max_length=30, unique=True)
    barcode_gtin = models.CharField('GTIN/EAN', max_length=14, blank=True,
                                    validators=[fiscal.validate_gtin],
                                    help_text='Deixe em branco para "SEM GTIN".')
    unit_commercial = models.CharField('Unidade comercial', max_length=3,
                                       choices=fiscal.UnidadeMedida.choices,
                                       default=fiscal.UnidadeMedida.UN)
    unit_taxable = models.CharField('Unidade tributável', max_length=3,
                                    choices=fiscal.UnidadeMedida.choices,
                                    default=fiscal.UnidadeMedida.UN)

    # ── Fiscal (Simples Nacional) ────────────────────────────────
    origem = models.CharField('Origem da mercadoria', max_length=1,
                              choices=fiscal.Origem.choices, default=fiscal.Origem.N_0)
    ncm = models.CharField('NCM', max_length=8, validators=[fiscal.validate_ncm])
    cest = models.CharField('CEST', max_length=7, blank=True, validators=[fiscal.validate_cest])
    cfop = models.CharField('CFOP', max_length=4, choices=fiscal.CFOP.choices,
                            default=fiscal.CFOP.F5102, validators=[fiscal.validate_cfop])
    csosn = models.CharField('CSOSN', max_length=3, choices=fiscal.CSOSN.choices,
                             default=fiscal.CSOSN.C102)
    icms_aliquota = models.DecimalField('Alíquota ICMS próprio (%)', max_digits=5, decimal_places=2,
                                        null=True, blank=True, validators=[MinValueValidator(ZERO)])
    pis_cst = models.CharField('CST PIS', max_length=2, choices=fiscal.CST_PIS_COFINS.choices,
                               default=fiscal.CST_PIS_COFINS.T49)
    pis_aliquota = models.DecimalField('Alíquota PIS (%)', max_digits=5, decimal_places=2,
                                       default=0, validators=[MinValueValidator(ZERO)])
    cofins_cst = models.CharField('CST COFINS', max_length=2, choices=fiscal.CST_PIS_COFINS.choices,
                                  default=fiscal.CST_PIS_COFINS.T49)
    cofins_aliquota = models.DecimalField('Alíquota COFINS (%)', max_digits=5, decimal_places=2,
                                          default=0, validators=[MinValueValidator(ZERO)])
    fisco_info = models.CharField('Informação adicional ao fisco', max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Item do Cardápio'
        verbose_name_plural = 'Itens do Cardápio'
        ordering = ['category__display_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'sector']),
            models.Index(fields=['ncm']),
        ]

    def __str__(self):
        return f'{self.name} ({self.sku})'

    @property
    def sujeito_a_st(self):
        return self.csosn in fiscal.CSOSN_COM_ST

    @property
    def fiscal_snapshot(self):
        """Dados fiscais congelados no item do pedido no momento da venda."""
        return {
            'fiscal_ncm': self.ncm,
            'fiscal_cest': self.cest,
            'fiscal_cfop': self.cfop,
            'fiscal_csosn': self.csosn,
            'fiscal_origem': self.origem,
            'fiscal_unit': self.unit_commercial,
        }
