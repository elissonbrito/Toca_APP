"""
Orders services - regra de negócio de comandas fora das views.

As views cuidam de HTTP + auditoria; aqui fica o domínio (transições de
status, efeito colateral na mesa, recálculo de total).
"""
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.tables.models import TableStatus
from .models import Order, OrderItem, OrderStatus, ItemStatus

CLOSED_STATUSES = {OrderStatus.FINALIZADO, OrderStatus.CANCELADO}


class OrderService:
    @staticmethod
    @transaction.atomic
    def open_order(*, table, opened_by, customer_name='', people_count=1, observations=''):
        """Abre uma comanda e marca a mesa como ocupada."""
        if table.orders.exclude(status__in=CLOSED_STATUSES).exists():
            raise ValidationError({'table': 'Já existe uma comanda aberta para esta mesa.'})

        order = Order.objects.create(
            table=table,
            opened_by=opened_by,
            customer_name=customer_name,
            people_count=people_count,
            observations=observations,
        )
        if table.status != TableStatus.OCUPADA:
            table.status = TableStatus.OCUPADA
            table.save(update_fields=['status', 'updated_at'])
        return order

    @staticmethod
    @transaction.atomic
    def add_item(order, *, menu_item=None, product_name=None, quantity=1,
                 unit_price=None, sector=None, observations=''):
        """Adiciona um item à comanda e recalcula o total.

        Se ``menu_item`` for informado, nome/preço/setor saem do cardápio (salvo
        override explícito) e os dados fiscais são congelados no item (snapshot).
        Caso contrário, aceita lançamento por texto livre (retrocompatível).
        """
        if order.status in CLOSED_STATUSES:
            raise ValidationError(
                'Não é possível adicionar itens a um pedido finalizado ou cancelado.'
            )

        fiscal_snapshot = {}
        if menu_item is not None:
            if not menu_item.is_active:
                raise ValidationError({'menu_item': 'Este item do cardápio está inativo.'})
            product_name = product_name or menu_item.name
            unit_price = menu_item.price if unit_price is None else unit_price
            sector = sector or menu_item.sector
            fiscal_snapshot = menu_item.fiscal_snapshot

        if not product_name or unit_price is None:
            raise ValidationError('Informe um item do cardápio ou nome e preço do produto.')

        item = OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            sector=sector or 'COZINHA',
            observations=observations,
            **fiscal_snapshot,
        )
        order.recalculate_total()
        return item

    @staticmethod
    @transaction.atomic
    def cancel_item(order, item):
        """Cancela (soft) um item e recalcula o total."""
        if item.status == ItemStatus.CANCELADO:
            return item
        item.status = ItemStatus.CANCELADO
        item.save(update_fields=['status', 'updated_at'])
        order.recalculate_total()
        return item

    ACTIVE_ITEM_STATUSES = {ItemStatus.PENDENTE, ItemStatus.PREPARANDO}

    @staticmethod
    @transaction.atomic
    def set_item_status(item, new_status):
        """Transição de status de um item (usada pela cozinha/parrilla).

        Retorna (status_anterior, item). Quando o item fica PRONTO e não há
        mais itens pendentes/preparando, a comanda inteira vira PRONTO.
        """
        if new_status not in ItemStatus.values:
            raise ValidationError({'status': 'Status inválido.'})

        old_status = item.status
        if old_status == new_status:
            return old_status, item

        item.status = new_status
        item.save(update_fields=['status', 'updated_at'])

        order = item.order
        if new_status == ItemStatus.PRONTO:
            remaining = order.items.filter(status__in=OrderService.ACTIVE_ITEM_STATUSES).exists()
            if not remaining and order.status not in CLOSED_STATUSES:
                order.status = OrderStatus.PRONTO
                order.save(update_fields=['status'])
        elif new_status in OrderService.ACTIVE_ITEM_STATUSES and order.status == OrderStatus.PRONTO:
            # Voltou a ter item em preparo: comanda deixa de estar "pronta".
            order.status = OrderStatus.PREPARANDO
            order.save(update_fields=['status'])

        return old_status, item

    @staticmethod
    @transaction.atomic
    def change_status(order, new_status):
        """Aplica uma transição de status na comanda.

        Retorna (status_anterior, order). Ao finalizar, fecha a comanda e
        manda a mesa para limpeza.
        """
        if new_status not in OrderStatus.values:
            raise ValidationError({'status': 'Status inválido.'})

        old_status = order.status
        if old_status == new_status:
            return old_status, order

        order.status = new_status
        update_fields = ['status']

        if new_status == OrderStatus.FINALIZADO:
            order.closed_at = timezone.now()
            update_fields.append('closed_at')
            order.table.status = TableStatus.LIMPEZA
            order.table.save(update_fields=['status', 'updated_at'])
        elif new_status == OrderStatus.CANCELADO:
            order.closed_at = timezone.now()
            update_fields.append('closed_at')
            order.table.status = TableStatus.LIVRE
            order.table.save(update_fields=['status', 'updated_at'])

        order.save(update_fields=update_fields)
        return old_status, order
