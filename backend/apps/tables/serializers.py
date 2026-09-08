from rest_framework import serializers
from .models import Table


class TableSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    active_order_id = serializers.SerializerMethodField()
    active_order_status = serializers.SerializerMethodField()

    class Meta:
        model = Table
        fields = ['id', 'number', 'seats', 'status', 'status_display', 'observation',
                  'active_order_id', 'active_order_status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def _active_order(self, obj):
        return (obj.orders
                .exclude(status__in=['FINALIZADO', 'CANCELADO'])
                .order_by('-created_at')
                .first())

    def get_active_order_id(self, obj):
        order = self._active_order(obj)
        return order.id if order else None

    def get_active_order_status(self, obj):
        order = self._active_order(obj)
        return order.status if order else None

    def validate_number(self, value):
        instance = self.instance
        qs = Table.objects.filter(number=value)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Já existe uma mesa com este número.')
        return value
