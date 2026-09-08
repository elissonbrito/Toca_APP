"""
Orders app models - Comandas and Order Items.
"""
from django.db import models
from django.conf import settings


class OrderStatus(models.TextChoices):
    ABERTO = 'ABERTO', 'Aberto'
    PREPARANDO = 'PREPARANDO', 'Preparando'
    PRONTO = 'PRONTO', 'Pronto'
    FECHAMENTO = 'FECHAMENTO', 'Conta fechada (aguardando caixa)'
    FINALIZADO = 'FINALIZADO', 'Finalizado'
    CANCELADO = 'CANCELADO', 'Cancelado'


class ItemSector(models.TextChoices):
    COZINHA = 'COZINHA', 'Cozinha'
    PARRILLA = 'PARRILLA', 'Parrilla'
    BAR = 'BAR', 'Bar'


class ItemStatus(models.TextChoices):
    PENDENTE = 'PENDENTE', 'Pendente'
    PREPARANDO = 'PREPARANDO', 'Preparando'
    PRONTO = 'PRONTO', 'Pronto'
    ENTREGUE = 'ENTREGUE', 'Entregue'
    CANCELADO = 'CANCELADO', 'Cancelado'


class Order(models.Model):
    """Comanda / Order model.

    ``table`` pode ser nulo: uma comanda pode nascer vinculada a uma senha
    (cliente pedindo enquanto espera) e só depois receber a mesa.
    """
    table = models.ForeignKey(
        'tables.Table',
        on_delete=models.PROTECT,
        related_name='orders',
        null=True, blank=True,
        verbose_name='Mesa'
    )
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='opened_orders',
        verbose_name='Aberto por'
    )
    queue_ticket = models.ForeignKey(
        'queue.QueueTicket',
        on_delete=models.SET_NULL,
        related_name='orders',
        null=True, blank=True,
        verbose_name='Senha de origem',
    )
    status = models.CharField(
        'Status',
        max_length=15,
        choices=OrderStatus.choices,
        default=OrderStatus.ABERTO
    )
    total_amount = models.DecimalField('Total', max_digits=10, decimal_places=2, default=0)
    customer_name = models.CharField('Nome do Cliente', max_length=150, blank=True)
    people_count = models.PositiveIntegerField('Número de Pessoas', default=1)
    observations = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField('Aberto em', auto_now_add=True)
    closed_at = models.DateTimeField('Fechado em', null=True, blank=True)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']

    def __str__(self):
        if self.table_id:
            return f'Pedido #{self.id} - Mesa {self.table.number}'
        if self.queue_ticket_id:
            return f'Pedido #{self.id} - Senha {self.queue_ticket.code}'
        return f'Pedido #{self.id}'

    def recalculate_total(self):
        from django.db.models import Sum
        total = self.items.filter(
            status__in=[ItemStatus.PENDENTE, ItemStatus.PREPARANDO, ItemStatus.PRONTO, ItemStatus.ENTREGUE]
        ).aggregate(total=Sum('total_price'))['total'] or 0
        self.total_amount = total
        self.save(update_fields=['total_amount'])


class OrderItem(models.Model):
    """Individual item in an order."""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Pedido'
    )
    menu_item = models.ForeignKey(
        'menu.MenuItem',
        on_delete=models.PROTECT,
        related_name='order_items',
        null=True, blank=True,
        verbose_name='Item do cardápio',
    )
    product_name = models.CharField('Produto', max_length=200)
    quantity = models.PositiveIntegerField('Quantidade', default=1)
    unit_price = models.DecimalField('Preço Unitário', max_digits=10, decimal_places=2)
    total_price = models.DecimalField('Total', max_digits=10, decimal_places=2)
    sector = models.CharField(
        'Setor',
        max_length=10,
        choices=ItemSector.choices,
        default=ItemSector.COZINHA
    )

    # Atribuição — quem lançou e (se for o caso) quem retirou o item da conta.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='launched_items',
        null=True, blank=True,
        verbose_name='Lançado por',
    )
    removed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='removed_items',
        null=True, blank=True,
        verbose_name='Retirado por',
    )
    removed_at = models.DateTimeField('Retirado em', null=True, blank=True)

    # Snapshot fiscal — congelado no momento da venda (imutável, base da NFC-e).
    fiscal_ncm = models.CharField('NCM', max_length=8, blank=True)
    fiscal_cest = models.CharField('CEST', max_length=7, blank=True)
    fiscal_cfop = models.CharField('CFOP', max_length=4, blank=True)
    fiscal_csosn = models.CharField('CSOSN', max_length=3, blank=True)
    fiscal_origem = models.CharField('Origem', max_length=1, blank=True)
    fiscal_unit = models.CharField('Unidade', max_length=3, blank=True)
    status = models.CharField(
        'Status',
        max_length=15,
        choices=ItemStatus.choices,
        default=ItemStatus.PENDENTE
    )
    observations = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'

    def __str__(self):
        return f'{self.quantity}x {self.product_name}'

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
