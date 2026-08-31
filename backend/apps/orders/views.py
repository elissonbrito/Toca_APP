from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from .models import Order, OrderStatus
from .serializers import (
    OrderSerializer, OrderCreateSerializer,
    OrderItemSerializer, OrderItemCreateSerializer,
)
from .services import OrderService
from apps.users.permissions import IsManager, IsFloorStaff, IsFloorStaffOrCaixa, IsCaixa
from apps.audit.services import AuditService

CAIXA_ROLES = {'CAIXA', 'ADM_MAXIMO', 'GERENTE'}


class OrderViewSet(viewsets.ModelViewSet):
    queryset = (Order.objects
                .select_related('table', 'opened_by', 'queue_ticket')
                .prefetch_related('items')
                .all())
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status', 'table']
    search_fields = ['customer_name', 'table__number']

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsCaixa()]                      # excluir conta -> caixa/gerência
        if self.action in ['update', 'partial_update']:
            return [IsManager()]
        if self.action == 'create':
            return [IsFloorStaff()]
        if self.action == 'remove_item':
            return [IsCaixa()]                      # só o caixa exclui itens lançados
        if self.action == 'close_bill':
            return [IsFloorStaffOrCaixa()]
        if self.action == 'reopen_bill':
            return [IsCaixa()]
        # list, retrieve, update_status, add_item
        return [IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        """DELETE numa comanda = cancelar a conta (soft), nunca apagar do banco.

        Preserva pagamentos/NFC-e. Só o caixa/gerência (get_permissions).
        """
        order = self.get_object()
        old_status, order = OrderService.change_status(order, OrderStatus.CANCELADO)
        AuditService.log(
            user=request.user, action='UPDATE', entity='Order', entity_id=order.id,
            details=f'Conta do Pedido #{order.id} cancelada pelo caixa ({old_status} -> CANCELADO)',
            request=request,
        )
        return Response(OrderSerializer(order).data)

    # --- create -----------------------------------------------------------
    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = OrderService.open_order(opened_by=request.user, **serializer.validated_data)
        AuditService.log(
            user=request.user, action='CREATE', entity='Order', entity_id=order.id,
            details=f'Comanda #{order.id} aberta na Mesa {order.table.number}',
            request=request,
        )
        return Response(OrderSerializer(order).data, status=201)

    # --- itens ----------------------------------------------------------
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        order = self.get_object()
        serializer = OrderItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = OrderService.add_item(order, **serializer.validated_data)
        order.refresh_from_db()
        AuditService.log(
            user=request.user, action='CREATE', entity='OrderItem', entity_id=item.id,
            details=f'{item.quantity}x {item.product_name} adicionado ao Pedido #{order.id}',
            request=request,
        )
        return Response(OrderItemSerializer(item).data, status=201)

    @action(detail=True, methods=['delete'], url_path='items/(?P<item_id>[^/.]+)')
    def remove_item(self, request, pk=None, item_id=None):
        order = self.get_object()
        item = order.items.filter(pk=item_id).first()
        if item is None:
            return Response({'detail': 'Item não encontrado.'}, status=404)
        OrderService.cancel_item(order, item)
        AuditService.log(
            user=request.user, action='UPDATE', entity='OrderItem', entity_id=item.id,
            details=f'Caixa cancelou o item {item.product_name} no Pedido #{order.id}',
            request=request,
        )
        return Response({'detail': 'Item cancelado.'})

    # --- conta / status ------------------------------------------------
    @action(detail=True, methods=['post'])
    def close_bill(self, request, pk=None):
        """Fechar conta: manda a comanda para o caixa."""
        order = self.get_object()
        old_status, order = OrderService.close_bill(order)
        AuditService.log(
            user=request.user, action='UPDATE', entity='Order', entity_id=order.id,
            details=f'Conta do Pedido #{order.id} fechada ({old_status} -> FECHAMENTO)',
            request=request,
        )
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=['post'])
    def reopen_bill(self, request, pk=None):
        order = OrderService.reopen_bill(self.get_object())
        AuditService.log(
            user=request.user, action='UPDATE', entity='Order', entity_id=order.id,
            details=f'Conta do Pedido #{order.id} reaberta', request=request,
        )
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        if (new_status == OrderStatus.CANCELADO
                and request.user.role not in CAIXA_ROLES):
            raise PermissionDenied('Apenas o caixa ou a gerência podem cancelar a conta.')
        old_status, order = OrderService.change_status(order, new_status)
        AuditService.log(
            user=request.user, action='UPDATE', entity='Order', entity_id=order.id,
            details=f'Pedido #{order.id} alterado de {old_status} para {order.status}',
            request=request,
        )
        return Response(OrderSerializer(order).data)
