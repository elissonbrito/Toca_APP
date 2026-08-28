from django.db import models
from django.conf import settings


class TicketStatus(models.TextChoices):
    AGUARDANDO = 'AGUARDANDO', 'Aguardando'
    CHAMADO = 'CHAMADO', 'Chamado'
    SENTADO = 'SENTADO', 'Na mesa'
    FINALIZADO = 'FINALIZADO', 'Finalizado'
    CANCELADO = 'CANCELADO', 'Cancelado'


class QueueTicket(models.Model):
    code = models.CharField('Código', max_length=10, unique=True)
    customer_name = models.CharField('Nome do Cliente', max_length=150, blank=True)
    people_count = models.PositiveIntegerField('Número de Pessoas', default=1)
    status = models.CharField(
        'Status',
        max_length=15,
        choices=TicketStatus.choices,
        default=TicketStatus.AGUARDANDO
    )
    table = models.ForeignKey(
        'tables.Table',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='queue_tickets',
        verbose_name='Mesa destinada',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    called_at = models.DateTimeField(null=True, blank=True)
    called_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='called_tickets'
    )

    class Meta:
        verbose_name = 'Senha'
        verbose_name_plural = 'Senhas'
        ordering = ['created_at']

    def __str__(self):
        return f'Senha {self.code} - {self.customer_name or "Anônimo"}'

    @classmethod
    def generate_code(cls):
        """Generate next sequential ticket code."""
        from django.utils import timezone
        today = timezone.now().date()
        prefix = today.strftime('%d%m')
        last = cls.objects.filter(code__startswith=prefix).order_by('-code').first()
        if last:
            try:
                seq = int(last.code[4:]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f'{prefix}{seq:03d}'
