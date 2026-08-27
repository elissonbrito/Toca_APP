from rest_framework import serializers

from .models import FiscalSettings, Invoice


class FiscalSettingsSerializer(serializers.ModelSerializer):
    pronto_para_transmitir = serializers.BooleanField(read_only=True)
    faltando = serializers.SerializerMethodField()

    class Meta:
        model = FiscalSettings
        fields = [
            'razao_social', 'nome_fantasia', 'cnpj', 'inscricao_estadual', 'regime_tributario',
            'uf', 'municipio_ibge', 'municipio_nome', 'logradouro', 'numero', 'bairro', 'cep', 'fone',
            'environment', 'serie_nfce', 'proximo_numero', 'csc_id',
            'certificado_path', 'pronto_para_transmitir', 'faltando', 'updated_at',
        ]
        read_only_fields = ['updated_at']
        extra_kwargs = {
            'csc_token': {'write_only': True},
            'certificado_senha': {'write_only': True},
        }

    def get_faltando(self, obj):
        return obj.missing_for_transmission()


class FiscalSettingsWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalSettings
        exclude = ['id']


class InvoiceSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    table_number = serializers.IntegerField(source='order.table.number', read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'order_id', 'table_number', 'numero', 'serie', 'chave_acesso', 'ambiente',
            'status', 'status_display', 'valor_total', 'protocolo_autorizacao',
            'qr_code_data', 'motivo', 'created_at', 'autorizada_em',
        ]
