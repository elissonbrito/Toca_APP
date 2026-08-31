from rest_framework import serializers
from .models import Table


class TableSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    active_order_id = serializers.SerializerMethodField()

    class Meta:
        model = Table
        fields = ['id', 'number', 'seats', 'status', 'status_display', 'observation',
                  'active_order_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_active_order_id(self, obj):
        order = obj.orders.exclude(status__in=['FINALIZADO', 'CANCELADO']).order_by('-created_at').first()
        return order.id if order else None

    def validate_number(self, value):
        instance = self.instance
        qs = Table.objects.filter(number=value)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Já existe uma mesa com este número.')
        return value
