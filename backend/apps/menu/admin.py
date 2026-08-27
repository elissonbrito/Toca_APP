from django.contrib import admin
from django.utils.html import format_html

from .models import MenuCategory, MenuItem
from .services import FiscalConferenceService


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'sector', 'price', 'csosn', 'ncm', 'is_active', 'fiscal_ok')
    list_filter = ('is_active', 'sector', 'category', 'csosn', 'origem')
    search_fields = ('name', 'sku', 'ncm', 'barcode_gtin')
    list_select_related = ('category',)
    readonly_fields = ('created_at', 'updated_at', 'fiscal_report')
    fieldsets = (
        ('Operacional', {
            'fields': ('category', 'name', 'description', 'sector', 'price',
                       'preparation_minutes', 'is_active'),
        }),
        ('Comercial', {
            'fields': ('sku', 'barcode_gtin', 'unit_commercial', 'unit_taxable'),
        }),
        ('Fiscal — Simples Nacional', {
            'fields': ('origem', 'ncm', 'cest', 'cfop', 'csosn', 'icms_aliquota',
                       'pis_cst', 'pis_aliquota', 'cofins_cst', 'cofins_aliquota', 'fisco_info',
                       'fiscal_report'),
        }),
        ('Datas', {'fields': ('created_at', 'updated_at')}),
    )

    @admin.display(description='Fiscal', boolean=True)
    def fiscal_ok(self, obj):
        return FiscalConferenceService.check_item(obj)['ok']

    @admin.display(description='Conferência fiscal')
    def fiscal_report(self, obj):
        if obj.pk is None:
            return '—'
        r = FiscalConferenceService.check_item(obj)
        if r['ok'] and not r['warnings']:
            return format_html('<b style="color:green">Conforme</b>')
        rows = ''.join(f'<li style="color:#b00">{e}</li>' for e in r['errors'])
        rows += ''.join(f'<li style="color:#b80">{w}</li>' for w in r['warnings'])
        return format_html('<ul style="margin:0;padding-left:1em">{}</ul>', format_html(rows))
