from rest_framework import serializers
from .models import QueueTicket


class QueueTicketSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_category_display = serializers.CharField(source='get_priority_category_display', read_only=True)
    is_priority = serializers.BooleanField(read_only=True)
    priority_rank = serializers.IntegerField(read_only=True)
    table_number = serializers.SerializerMethodField()
    active_order_id = serializers.SerializerMethodField()

    class Meta:
        model = QueueTicket
        fields = ['id', 'code', 'customer_name', 'people_count', 'status', 'status_display',
                  'priority_category', 'priority_category_display', 'is_priority', 'priority_rank',
                  'table', 'table_number', 'active_order_id', 'created_at', 'called_at']
        read_only_fields = ['id', 'code', 'table', 'created_at', 'called_at']

    def get_table_number(self, obj):
        return obj.table.number if obj.table_id else None

    def get_active_order_id(self, obj):
        order = obj.orders.exclude(status__in=['FINALIZADO', 'CANCELADO']).first()
        return order.id if order else None


class QueueTicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueueTicket
        fields = ['customer_name', 'people_count', 'priority_category']
        extra_kwargs = {'priority_category': {'required': False}}


class QueueTicketEditSerializer(serializers.ModelSerializer):
    """Edição pontual: nome do cliente (aceita qualquer texto) e quantidade
    de pessoas (pode zerar — 0 é um valor válido)."""

    class Meta:
        model = QueueTicket
        fields = ['customer_name', 'people_count']
