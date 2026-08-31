"""
Tables app models.
"""
from django.db import models


class TableStatus(models.TextChoices):
    LIVRE = 'LIVRE', 'Livre'
    OCUPADA = 'OCUPADA', 'Ocupada'
    CONTA = 'CONTA', 'Aguardando pagamento'
    RESERVADA = 'RESERVADA', 'Reservada'
    LIMPEZA = 'LIMPEZA', 'Em Limpeza'


class Table(models.Model):
    """Restaurant table model."""
    number = models.PositiveIntegerField('Número', unique=True)
    seats = models.PositiveIntegerField('Lugares', default=4)
    status = models.CharField(
        'Status',
        max_length=15,
        choices=TableStatus.choices,
        default=TableStatus.LIVRE
    )
    observation = models.TextField('Observação', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mesa'
        verbose_name_plural = 'Mesas'
        ordering = ['number']

    def __str__(self):
        return f'Mesa {self.number} - {self.get_status_display()}'
