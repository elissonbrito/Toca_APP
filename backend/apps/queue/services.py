"""
Queue services - regra de negócio da fila de senhas.
"""
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import QueueTicket, TicketStatus

OPEN_STATUSES = {TicketStatus.AGUARDANDO, TicketStatus.CHAMADO}


class QueueService:
    @staticmethod
    @transaction.atomic
    def issue_ticket(*, customer_name='', people_count=1):
        """Emite uma nova senha com código sequencial do dia."""
        return QueueTicket.objects.create(
            code=QueueTicket.generate_code(),
            customer_name=customer_name,
            people_count=people_count,
        )

    @staticmethod
    @transaction.atomic
    def call_next(called_by):
        """Chama a próxima senha aguardando. Lança ValidationError se a fila estiver vazia."""
        ticket = (
            QueueTicket.objects
            .select_for_update()
            .filter(status=TicketStatus.AGUARDANDO)
            .order_by('created_at')
            .first()
        )
        if ticket is None:
            raise ValidationError('Nenhuma senha na fila.')
        ticket.status = TicketStatus.CHAMADO
        ticket.called_at = timezone.now()
        ticket.called_by = called_by
        ticket.save(update_fields=['status', 'called_at', 'called_by'])
        return ticket

    @staticmethod
    def set_status(ticket, new_status):
        if new_status not in TicketStatus.values:
            raise ValidationError({'status': 'Status inválido.'})
        ticket.status = new_status
        ticket.save(update_fields=['status'])
        return ticket
