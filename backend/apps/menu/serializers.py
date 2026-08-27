from rest_framework import serializers

from .models import MenuCategory, MenuItem
from .services import FiscalConferenceService


class MenuCategorySerializer(serializers.ModelSerializer):
    item_count = serializers.IntegerField(source='items.count', read_only=True)

    class Meta:
        model = MenuCategory
        fields = ['id', 'name', 'slug', 'display_order', 'is_active', 'item_count',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    sector_display = serializers.CharField(source='get_sector_display', read_only=True)
    origem_display = serializers.CharField(source='get_origem_display', read_only=True)
    csosn_display = serializers.CharField(source='get_csosn_display', read_only=True)
    cfop_display = serializers.CharField(source='get_cfop_display', read_only=True)
    sujeito_a_st = serializers.BooleanField(read_only=True)
    fiscal_status = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = [
            'id', 'category', 'category_name', 'name', 'description', 'sector', 'sector_display',
            'price', 'preparation_minutes', 'is_active',
            'sku', 'barcode_gtin', 'unit_commercial', 'unit_taxable',
            'origem', 'origem_display', 'ncm', 'cest', 'cfop', 'cfop_display',
            'csosn', 'csosn_display', 'icms_aliquota',
            'pis_cst', 'pis_aliquota', 'cofins_cst', 'cofins_aliquota', 'fisco_info',
            'sujeito_a_st', 'fiscal_status', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_fiscal_status(self, obj):
        r = FiscalConferenceService.check_item(obj)
        return {'ok': r['ok'], 'errors': r['errors'], 'warnings': r['warnings']}

    def validate(self, attrs):
        merged = {**{f: getattr(self.instance, f, None) for f in (
            'csosn', 'cest', 'icms_aliquota')}, **attrs}
        csosn = merged.get('csosn')
        from . import fiscal
        if csosn in fiscal.CSOSN_COM_ST and not fiscal._digits(merged.get('cest') or ''):
            raise serializers.ValidationError(
                {'cest': f'CEST é obrigatório para CSOSN {csosn} (mercadoria com ICMS-ST).'})
        if csosn in fiscal.CSOSN_COM_ICMS_PROPRIO and merged.get('icms_aliquota') in (None, ''):
            raise serializers.ValidationError(
                {'icms_aliquota': f'Alíquota de ICMS próprio é obrigatória para CSOSN {csosn}.'})
        return attrs
