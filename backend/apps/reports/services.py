"""
Reports services - agregações gerenciais para metas e produtividade.

Toda transação já fica registrada (Payment + OrderItem com ``created_by`` /
``removed_by``). Aqui só se consolida por mês.
"""
from datetime import date

from django.db.models import Sum, Count, Q, DecimalField
from django.db.models.functions import Coalesce

from apps.orders.models import OrderItem, ItemStatus

# Itens que contam como "vendidos" (qualquer coisa que não foi cancelada).
SOLD_STATUSES = [
    ItemStatus.PENDENTE, ItemStatus.PREPARANDO, ItemStatus.PRONTO, ItemStatus.ENTREGUE,
]
_DECIMAL = DecimalField(max_digits=12, decimal_places=2)


def month_bounds(year, month):
    start = date(year, month, 1)
    end = date(year + (month == 12), (month % 12) + 1, 1)
    return start, end


class ReportsService:
    @staticmethod
    def _month_items(year, month):
        start, end = month_bounds(year, month)
        return OrderItem.objects.filter(
            created_at__date__gte=start, created_at__date__lt=end,
        )

    @staticmethod
    def sales_by_waiter(year, month):
        rows = (
            ReportsService._month_items(year, month)
            .filter(created_by__isnull=False)
            .values('created_by', 'created_by__name')
            .annotate(
                sold_items=Count('id', filter=Q(status__in=SOLD_STATUSES)),
                sold_qty=Coalesce(Sum('quantity', filter=Q(status__in=SOLD_STATUSES)), 0),
                revenue=Coalesce(
                    Sum('total_price', filter=Q(status__in=SOLD_STATUSES)), 0,
                    output_field=_DECIMAL,
                ),
                removed_items=Count('id', filter=Q(status=ItemStatus.CANCELADO)),
                removed_value=Coalesce(
                    Sum('total_price', filter=Q(status=ItemStatus.CANCELADO)), 0,
                    output_field=_DECIMAL,
                ),
            )
            .order_by('-revenue')
        )
        return [
            {
                'waiter_id': r['created_by'],
                'waiter_name': r['created_by__name'],
                'sold_items': r['sold_items'],
                'sold_qty': r['sold_qty'],
                'revenue': float(r['revenue']),
                'removed_items': r['removed_items'],
                'removed_value': float(r['removed_value']),
            }
            for r in rows
        ]

    @staticmethod
    def waiter_detail(year, month, waiter_id):
        rows = (
            ReportsService._month_items(year, month)
            .filter(created_by_id=waiter_id, status__in=SOLD_STATUSES)
            .values('product_name')
            .annotate(qty=Sum('quantity'), revenue=Sum('total_price'))
            .order_by('-qty')
        )
        return [
            {'product_name': r['product_name'], 'qty': r['qty'],
             'revenue': float(r['revenue'] or 0)}
            for r in rows
        ]

    @staticmethod
    def item_ranking(year, month):
        rows = (
            ReportsService._month_items(year, month)
            .filter(status__in=SOLD_STATUSES)
            .values('product_name')
            .annotate(
                qty=Sum('quantity'),
                revenue=Sum('total_price'),
                orders=Count('order', distinct=True),
            )
            .order_by('-qty')
        )
        return [
            {'product_name': r['product_name'], 'qty': r['qty'],
             'revenue': float(r['revenue'] or 0), 'orders': r['orders']}
            for r in rows
        ]
