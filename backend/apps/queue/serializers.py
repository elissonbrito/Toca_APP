from rest_framework import serializers
from .models import QueueTicket


class QueueTicketSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = QueueTicket
        fields = ['id', 'code', 'customer_name', 'people_count', 'status', 'status_display', 'created_at', 'called_at']
        read_only_fields = ['id', 'code', 'created_at', 'called_at']


class QueueTicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueueTicket
        fields = ['customer_name', 'people_count']
