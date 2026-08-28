from rest_framework import serializers
from .models import Order, OrderItem
from apps.users.serializers import UserSerializer
from apps.tables.serializers import TableSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sector_display = serializers.CharField(source='get_sector_display', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'menu_item', 'product_name', 'quantity', 'unit_price', 'total_price',
            'sector', 'sector_display', 'status', 'status_display',
            'observations', 'created_at', 'updated_at',
            'fiscal_ncm', 'fiscal_cest', 'fiscal_cfop', 'fiscal_csosn',
            'fiscal_origem', 'fiscal_unit',
        ]
        read_only_fields = [
            'id', 'total_price', 'created_at', 'updated_at',
            'fiscal_ncm', 'fiscal_cest', 'fiscal_cfop', 'fiscal_csosn',
            'fiscal_origem', 'fiscal_unit',
        ]


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """Lançamento de item na comanda — somente itens ativos do cardápio."""

    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity', 'observations']
        extra_kwargs = {
            'menu_item': {'required': True, 'allow_null': False},
            'quantity': {'min_value': 1},
        }

    def validate_menu_item(self, value):
        if value is None or not value.is_active:
            raise serializers.ValidationError('Selecione um item ativo do cardápio.')
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    opened_by = UserSerializer(read_only=True)
    table = TableSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'table', 'opened_by', 'status', 'status_display',
            'total_amount', 'customer_name', 'people_count', 'observations',
            'items', 'created_at', 'closed_at'
        ]
        read_only_fields = ['id', 'total_amount', 'created_at', 'closed_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['table', 'customer_name', 'people_count', 'observations']
