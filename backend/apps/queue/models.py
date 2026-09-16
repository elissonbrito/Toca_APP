from django.db import models
from django.conf import settings


class TicketStatus(models.TextChoices):
    AGUARDANDO = 'AGUARDANDO', 'Aguardando'
    CHAMADO = 'CHAMADO', 'Chamado'
    SENTADO = 'SENTADO', 'Na mesa'
    FINALIZADO = 'FINALIZADO', 'Finalizado'
    CANCELADO = 'CANCELADO', 'Cancelado'


class PriorityCategory(models.TextChoices):
    """Categorias de atendimento prioritário (Lei 10.048/2000 e alterações —
    prioridade especial para 80 anos ou mais introduzida pela Lei 13.466/2017;
    ajuste conforme a legislação municipal aplicável ao estabelecimento)."""
    NENHUMA = 'NENHUMA', 'Sem prioridade'
    IDOSO_80 = 'IDOSO_80', 'Idoso(a) — 80 anos ou mais'
    PCD = 'PCD', 'Pessoa com deficiência'
    IDOSO_60 = 'IDOSO_60', 'Idoso(a) — 60 a 79 anos'
    GESTANTE = 'GESTANTE', 'Gestante'
    LACTANTE = 'LACTANTE', 'Lactante'
    COLO = 'COLO', 'Pessoa com criança de colo'
    OBESIDADE = 'OBESIDADE', 'Pessoa com obesidade'


# Ordem de atendimento dentro da fila: 80+ tem atendimento imediato (rank 0,
# à frente das demais prioridades); as demais categorias prioritárias são
# equivalentes entre si e seguem ordem de chegada; sem prioridade vai por
# último (rank 2), também por ordem de chegada.
PRIORITY_RANK = {
    PriorityCategory.IDOSO_80: 0,
    PriorityCategory.PCD: 1,
    PriorityCategory.IDOSO_60: 1,
    PriorityCategory.GESTANTE: 1,
    PriorityCategory.LACTANTE: 1,
    PriorityCategory.COLO: 1,
    PriorityCategory.OBESIDADE: 1,
    PriorityCategory.NENHUMA: 2,
}


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
    priority_category = models.CharField(
        'Prioridade', max_length=10,
        choices=PriorityCategory.choices,
        default=PriorityCategory.NENHUMA,
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

    @property
    def is_priority(self):
        return self.priority_category != PriorityCategory.NENHUMA

    @property
    def priority_rank(self):
        return PRIORITY_RANK.get(self.priority_category, 2)

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
