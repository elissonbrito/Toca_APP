from rest_framework import serializers
from .models import CashRegister, Payment


class CashRegisterSerializer(serializers.ModelSerializer):
    opened_by_name = serializers.CharField(source='opened_by.name', read_only=True)
    closed_by_name = serializers.CharField(source='closed_by.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = CashRegister
        fields = [
            'id', 'opened_by', 'opened_by_name', 'closed_by', 'closed_by_name',
            'initial_amount', 'final_amount', 'status', 'status_display',
            'observations', 'opened_at', 'closed_at'
        ]
        read_only_fields = ['id', 'opened_by', 'closed_by', 'opened_at', 'closed_at']


class CashRegisterOpenSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashRegister
        fields = ['initial_amount', 'observations']


class PaymentSerializer(serializers.ModelSerializer):
    order_table = serializers.IntegerField(source='order.table.number', read_only=True, default=None)
    received_by_name = serializers.CharField(source='received_by.name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'order_table', 'cash_register', 'amount',
            'payment_method', 'payment_method_display', 'received_by',
            'received_by_name', 'observations', 'paid_at'
        ]
        read_only_fields = ['id', 'cash_register', 'received_by', 'paid_at']


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['order', 'amount', 'payment_method', 'observations']
