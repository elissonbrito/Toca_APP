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
    """Aceita um item do cardápio (menu_item) OU lançamento por texto livre."""
    product_name = serializers.CharField(required=False, allow_blank=True)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    sector = serializers.CharField(required=False)

    class Meta:
        model = OrderItem
        fields = ['menu_item', 'product_name', 'quantity', 'unit_price', 'sector', 'observations']

    def validate(self, attrs):
        if not attrs.get('menu_item') and not (attrs.get('product_name') and attrs.get('unit_price') is not None):
            raise serializers.ValidationError(
                'Informe "menu_item" ou então "product_name" e "unit_price".')
        return attrs


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
