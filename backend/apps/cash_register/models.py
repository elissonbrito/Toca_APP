from django.db import models
from django.conf import settings


class CashRegisterStatus(models.TextChoices):
    ABERTO = 'ABERTO', 'Aberto'
    FECHADO = 'FECHADO', 'Fechado'


class PaymentMethod(models.TextChoices):
    DINHEIRO = 'DINHEIRO', 'Dinheiro'
    PIX = 'PIX', 'PIX'
    DEBITO = 'DEBITO', 'Débito'
    CREDITO = 'CREDITO', 'Crédito'


class CashRegister(models.Model):
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='opened_registers',
        verbose_name='Aberto por'
    )
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='closed_registers',
        verbose_name='Fechado por'
    )
    initial_amount = models.DecimalField('Valor Inicial', max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField('Valor Final', max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(
        'Status',
        max_length=10,
        choices=CashRegisterStatus.choices,
        default=CashRegisterStatus.ABERTO
    )
    observations = models.TextField('Observações', blank=True)
    opened_at = models.DateTimeField('Aberto em', auto_now_add=True)
    closed_at = models.DateTimeField('Fechado em', null=True, blank=True)

    class Meta:
        verbose_name = 'Caixa'
        verbose_name_plural = 'Caixas'
        ordering = ['-opened_at']

    def __str__(self):
        return f'Caixa #{self.id} - {self.get_status_display()}'


class Payment(models.Model):
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name='Pedido'
    )
    cash_register = models.ForeignKey(
        CashRegister,
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name='Caixa'
    )
    amount = models.DecimalField('Valor', max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        'Método de Pagamento',
        max_length=10,
        choices=PaymentMethod.choices
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='received_payments',
        verbose_name='Recebido por'
    )
    observations = models.TextField('Observações', blank=True)
    paid_at = models.DateTimeField('Pago em', auto_now_add=True)

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-paid_at']

    def __str__(self):
        return f'Pagamento #{self.id} - R$ {self.amount}'
