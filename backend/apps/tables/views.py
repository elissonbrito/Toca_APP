from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Table
from .serializers import TableSerializer
from .services import TableService
from apps.users.permissions import IsManager
from apps.audit.services import AuditService


class TableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'seats']

    def get_permissions(self):
        # Criar/editar/remover mesa é ação de gestão; trocar status é operacional.
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsManager()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        table = serializer.save()
        AuditService.log(
            user=self.request.user, action='CREATE', entity='Table', entity_id=table.id,
            details=f'Mesa {table.number} criada', request=self.request,
        )

    def perform_update(self, serializer):
        table = serializer.save()
        AuditService.log(
            user=self.request.user, action='UPDATE', entity='Table', entity_id=table.id,
            details=f'Mesa {table.number} atualizada', request=self.request,
        )

    def perform_destroy(self, instance):
        AuditService.log(
            user=self.request.user, action='DELETE', entity='Table', entity_id=instance.id,
            details=f'Mesa {instance.number} removida', request=self.request,
        )
        instance.delete()

    @action(detail=True, methods=['post'], url_path='status')
    def set_status(self, request, pk=None):
        """POST /api/tables/{id}/status/ { status } - transição operacional de status."""
        table = self.get_object()
        old_status = table.status
        table = TableService.change_status(table, request.data.get('status'))
        AuditService.log(
            user=request.user, action='UPDATE', entity='Table', entity_id=table.id,
            details=f'Mesa {table.number}: status {old_status} -> {table.status}',
            request=request,
        )
        return Response(TableSerializer(table).data)
