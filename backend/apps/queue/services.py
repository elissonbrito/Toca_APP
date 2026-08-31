"""
Queue services - regra de negócio da fila de senhas.
"""
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.tables.models import TableStatus
from .models import QueueTicket, TicketStatus

OPEN_STATUSES = {TicketStatus.AGUARDANDO, TicketStatus.CHAMADO}
CLOSED_TICKET_STATUSES = {TicketStatus.FINALIZADO, TicketStatus.CANCELADO}


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

    @staticmethod
    def active_order(ticket):
        """Comanda em aberto da senha (a que o cliente usa enquanto espera), se houver."""
        return ticket.orders.exclude(status__in=['FINALIZADO', 'CANCELADO']).first()

    @staticmethod
    @transaction.atomic
    def open_order_for_ticket(ticket, *, opened_by):
        """Abre uma comanda vinculada à senha, ainda SEM mesa.

        Permite lançar itens do cliente enquanto ele aguarda. Ao destinar a
        senha para uma mesa, esta comanda (com os itens) passa para a mesa.
        """
        if ticket.status in CLOSED_TICKET_STATUSES:
            raise ValidationError('Esta senha já foi finalizada ou cancelada.')
        existing = QueueService.active_order(ticket)
        if existing:
            return existing

        from apps.orders.services import OrderService
        return OrderService.open_order(
            opened_by=opened_by,
            queue_ticket=ticket,
            customer_name=ticket.customer_name,
            people_count=ticket.people_count,
        )

    @staticmethod
    @transaction.atomic
    def assign_table(ticket, table, *, seated_by, open_order=True):
        """Destina a senha a uma mesa.

        - Se a senha já tem comanda aberta (pedidos feitos na espera), essa
          comanda é vinculada à mesa — os itens vão junto.
        - Senão, e ``open_order=True``, abre uma comanda nova na mesa.
        Retorna (ticket, order|None). Só ADM/GERENTE/RECEPÇÃO chamam isto (view).
        """
        if ticket.status in CLOSED_TICKET_STATUSES:
            raise ValidationError('Esta senha já foi finalizada ou cancelada.')

        from apps.orders.services import OrderService
        existing = QueueService.active_order(ticket)

        if existing is None and table.status == TableStatus.OCUPADA and open_order:
            raise ValidationError({'table': f'Mesa {table.number} já está ocupada.'})

        ticket.table = table
        ticket.status = TicketStatus.SENTADO
        if not ticket.called_at:
            ticket.called_at = timezone.now()
            ticket.called_by = seated_by
        ticket.save(update_fields=['table', 'status', 'called_at', 'called_by'])

        order = None
        if existing is not None:
            order = OrderService.attach_table(existing, table)
        elif open_order:
            order = OrderService.open_order(
                table=table, opened_by=seated_by, queue_ticket=ticket,
                customer_name=ticket.customer_name, people_count=ticket.people_count,
            )
        elif table.status == TableStatus.LIVRE:
            table.status = TableStatus.RESERVADA
            table.save(update_fields=['status', 'updated_at'])
        return ticket, order
