"""
Kitchen / Parrilla - painel de preparo de itens, filtrado por setor.
"""
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.orders.models import OrderItem, ItemStatus, ItemSector
from apps.orders.serializers import OrderItemSerializer
from apps.orders.services import OrderService
from apps.users.permissions import IsKitchenOrParrilla
from apps.audit.services import AuditService

PREP_SECTORS = {ItemSector.COZINHA, ItemSector.PARRILLA, ItemSector.BAR}


class KitchenOrdersView(APIView):
    """GET /api/kitchen/orders/?sector=COZINHA - fila de itens a preparar."""
    permission_classes = [IsKitchenOrParrilla]

    def get(self, request):
        sector = request.query_params.get('sector', ItemSector.COZINHA)
        if sector not in PREP_SECTORS:
            return Response({'detail': 'Setor inválido.'}, status=400)
        items = (
            OrderItem.objects
            .filter(sector=sector, status__in=[ItemStatus.PENDENTE, ItemStatus.PREPARANDO])
            .select_related('order', 'order__table', 'order__queue_ticket')
            .order_by('created_at')
        )
        return Response(OrderItemSerializer(items, many=True).data)


class KitchenItemStatusView(APIView):
    """PATCH /api/kitchen/items/{item_id}/status/ { status } - avança o preparo."""
    permission_classes = [IsKitchenOrParrilla]

    def patch(self, request, item_id):
        item = OrderItem.objects.select_related('order').filter(pk=item_id).first()
        if item is None:
            return Response({'detail': 'Item não encontrado.'}, status=404)

        old_status, item = OrderService.set_item_status(item, request.data.get('status'))
        AuditService.log(
            user=request.user, action='UPDATE', entity='OrderItem', entity_id=item.id,
            details=(f'Item {item.product_name} ({item.sector}) '
                     f'{old_status} -> {item.status}'),
            request=request,
        )
        return Response(OrderItemSerializer(item).data)
