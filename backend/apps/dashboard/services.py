"""
Dashboard services - agregações administrativas (vendas, mesas, fila, produtos).
"""
from datetime import timedelta

from django.db.models import Sum, Count
from django.utils import timezone

from apps.orders.models import Order, OrderItem, OrderStatus
from apps.tables.models import Table, TableStatus
from apps.queue.models import QueueTicket, TicketStatus
from apps.cash_register.models import Payment

ACTIVE_ITEM_STATUSES = ['PENDENTE', 'PREPARANDO', 'PRONTO', 'ENTREGUE']


def _revenue_between(**date_filter):
    return Payment.objects.filter(**date_filter).aggregate(total=Sum('amount'))['total'] or 0


class DashboardService:
    @staticmethod
    def overview():
        today = timezone.now().date()
        month_start = today.replace(day=1)
        thirty_days_ago = today - timedelta(days=30)

        today_orders = Order.objects.filter(created_at__date=today)
        total_tables = Table.objects.count()
        occupied = Table.objects.filter(status=TableStatus.OCUPADA).count()

        top_products = list(
            OrderItem.objects
            .filter(order__created_at__date__gte=thirty_days_ago, status__in=ACTIVE_ITEM_STATUSES)
            .values('product_name')
            .annotate(total_qty=Sum('quantity'), total_revenue=Sum('total_price'))
            .order_by('-total_qty')[:10]
        )

        daily_revenue = [
            {
                'date': (today - timedelta(days=i)).strftime('%d/%m'),
                'revenue': float(_revenue_between(paid_at__date=today - timedelta(days=i))),
            }
            for i in range(6, -1, -1)
        ]

        return {
            'today': {
                'orders': today_orders.count(),
                'revenue': float(_revenue_between(paid_at__date=today)),
                'active_orders': Order.objects.filter(
                    status__in=[OrderStatus.ABERTO, OrderStatus.PREPARANDO]
                ).count(),
            },
            'monthly_revenue': float(_revenue_between(paid_at__date__gte=month_start)),
            'tables': {
                'total': total_tables,
                'occupied': occupied,
                'free': total_tables - occupied,
                'occupation_rate': round((occupied / total_tables * 100) if total_tables else 0, 1),
            },
            'queue': {
                'waiting': QueueTicket.objects.filter(status=TicketStatus.AGUARDANDO).count(),
            },
            'top_products': top_products,
            'daily_revenue': daily_revenue,
            'orders_by_status': list(today_orders.values('status').annotate(count=Count('id'))),
        }
