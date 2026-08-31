from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CashRegister, Payment
from .serializers import (
    CashRegisterSerializer, CashRegisterOpenSerializer,
    PaymentSerializer, PaymentCreateSerializer,
)
from .services import CashRegisterService, PaymentService
from apps.users.permissions import IsCaixa
from apps.audit.services import AuditService


class CashRegisterViewSet(viewsets.ModelViewSet):
    queryset = CashRegister.objects.select_related('opened_by', 'closed_by').all()
    serializer_class = CashRegisterSerializer
    permission_classes = [IsCaixa]
    http_method_names = ['get', 'post', 'head', 'options']

    def create(self, request, *args, **kwargs):
        serializer = CashRegisterOpenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        register = CashRegisterService.open(opened_by=request.user, **serializer.validated_data)
        AuditService.log(
            user=request.user, action='CREATE', entity='CashRegister', entity_id=register.id,
            details=f'Caixa #{register.id} aberto com R$ {register.initial_amount}',
            request=request,
        )
        return Response(CashRegisterSerializer(register).data, status=201)

    @action(detail=False, methods=['get'])
    def current(self, request):
        register = CashRegisterService.current_open()
        if register is None:
            return Response({'detail': 'Nenhum caixa aberto.'}, status=404)
        return Response(CashRegisterSerializer(register).data)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        register = CashRegisterService.close(
            self.get_object(),
            closed_by=request.user,
            final_amount=request.data.get('final_amount'),
            observations=request.data.get('observations', ''),
        )
        AuditService.log(
            user=request.user, action='UPDATE', entity='CashRegister', entity_id=register.id,
            details=f'Caixa #{register.id} fechado com R$ {register.final_amount}',
            request=request,
        )
        return Response(CashRegisterSerializer(register).data)

    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        data = CashRegisterService.report(self.get_object())
        data['register'] = CashRegisterSerializer(data['register']).data
        return Response(data)

    @action(detail=False, methods=['get'], url_path='pending-orders')
    def pending_orders(self, request):
        """Contas fechadas aguardando baixa no caixa (em evidência)."""
        from apps.orders.models import Order, OrderStatus
        from apps.orders.serializers import OrderSerializer

        orders = (Order.objects
                  .filter(status=OrderStatus.FECHAMENTO)
                  .select_related('table', 'opened_by', 'queue_ticket')
                  .prefetch_related('items')
                  .order_by('created_at'))
        return Response(OrderSerializer(orders, many=True).data)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related('order', 'order__table', 'cash_register', 'received_by').all()
    permission_classes = [IsCaixa]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer

    def create(self, request, *args, **kwargs):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment, invoice = PaymentService.register_payment(
            received_by=request.user,
            **serializer.validated_data,
        )
        AuditService.log(
            user=request.user, action='CREATE', entity='Payment', entity_id=payment.id,
            details=(f'Baixa de R$ {payment.amount} via {payment.payment_method} '
                     f'no Pedido #{payment.order_id}'
                     + (f' — NFC-e {invoice.get_status_display()}' if invoice else '')),
            request=request,
        )
        data = PaymentSerializer(payment).data
        if invoice is not None:
            from apps.fiscal.serializers import InvoiceSerializer
            data['invoice'] = InvoiceSerializer(invoice).data
        return Response(data, status=201)
