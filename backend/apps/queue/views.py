from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import QueueTicket, TicketStatus
from .serializers import QueueTicketSerializer, QueueTicketCreateSerializer
from .services import QueueService
from apps.users.permissions import IsManager, IsRecepcao
from apps.audit.services import AuditService


class QueueTicketViewSet(viewsets.ModelViewSet):
    queryset = QueueTicket.objects.select_related('called_by').all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

    def get_serializer_class(self):
        if self.action == 'create':
            return QueueTicketCreateSerializer
        return QueueTicketSerializer

    def get_permissions(self):
        if self.action == 'public_display':
            return []  # painel público, sem autenticação
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsManager()]
        # create, call_next, finalize, cancel
        return [IsRecepcao()]

    def create(self, request, *args, **kwargs):
        serializer = QueueTicketCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = QueueService.issue_ticket(**serializer.validated_data)
        AuditService.log(
            user=request.user, action='CREATE', entity='QueueTicket', entity_id=ticket.id,
            details=f'Senha {ticket.code} emitida', request=request,
        )
        return Response(QueueTicketSerializer(ticket).data, status=201)

    @action(detail=False, methods=['get'])
    def public_display(self, request):
        """Painel público: quantidade aguardando + última senha chamada."""
        waiting = QueueTicket.objects.filter(status=TicketStatus.AGUARDANDO).count()
        last_called = (
            QueueTicket.objects.filter(status=TicketStatus.CHAMADO)
            .order_by('-called_at').first()
        )
        return Response({
            'waiting_count': waiting,
            'last_called': QueueTicketSerializer(last_called).data if last_called else None,
        })

    @action(detail=False, methods=['post'])
    def call_next(self, request):
        ticket = QueueService.call_next(request.user)
        AuditService.log(
            user=request.user, action='UPDATE', entity='QueueTicket', entity_id=ticket.id,
            details=f'Senha {ticket.code} chamada', request=request,
        )
        return Response(QueueTicketSerializer(ticket).data)

    @action(detail=True, methods=['post'])
    def finalize(self, request, pk=None):
        ticket = QueueService.set_status(self.get_object(), TicketStatus.FINALIZADO)
        AuditService.log(
            user=request.user, action='UPDATE', entity='QueueTicket', entity_id=ticket.id,
            details=f'Senha {ticket.code} finalizada', request=request,
        )
        return Response(QueueTicketSerializer(ticket).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        ticket = QueueService.set_status(self.get_object(), TicketStatus.CANCELADO)
        AuditService.log(
            user=request.user, action='UPDATE', entity='QueueTicket', entity_id=ticket.id,
            details=f'Senha {ticket.code} cancelada', request=request,
        )
        return Response(QueueTicketSerializer(ticket).data)
