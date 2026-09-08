from rest_framework import serializers

from .models import Printer, PrintSettings, PrintJob


class PrinterSerializer(serializers.ModelSerializer):
    sector_display = serializers.CharField(source='get_sector_display', read_only=True)

    class Meta:
        model = Printer
        fields = ['id', 'name', 'sector', 'sector_display', 'qz_printer_name',
                  'is_active', 'copies', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PrintSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintSettings
        exclude = ['id']


class PrintJobSerializer(serializers.ModelSerializer):
    printer_name = serializers.CharField(source='printer.name', read_only=True, default=None)
    qz_printer_name = serializers.CharField(source='printer.qz_printer_name', read_only=True, default=None)
    copies = serializers.IntegerField(source='printer.copies', read_only=True, default=1)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PrintJob
        fields = ['id', 'order', 'order_item', 'printer', 'printer_name', 'qz_printer_name',
                  'copies', 'sector', 'title', 'body', 'status', 'status_display',
                  'error_message', 'created_at', 'printed_at']
        read_only_fields = fields
