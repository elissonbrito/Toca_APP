from django.contrib import admin

from .models import FiscalSettings, Invoice


@admin.register(FiscalSettings)
class FiscalSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'cnpj', 'uf', 'environment', 'serie_nfce', 'proximo_numero')
    fieldsets = (
        ('Emitente', {'fields': ('razao_social', 'nome_fantasia', 'cnpj',
                                 'inscricao_estadual', 'regime_tributario')}),
        ('Endereço', {'fields': ('uf', 'municipio_ibge', 'municipio_nome', 'logradouro',
                                 'numero', 'bairro', 'cep', 'fone')}),
        ('NFC-e', {'fields': ('environment', 'serie_nfce', 'proximo_numero',
                              'csc_id', 'csc_token')}),
        ('Certificado A1', {'fields': ('certificado_path', 'certificado_senha')}),
    )

    def has_add_permission(self, request):
        return not FiscalSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'numero', 'serie', 'status', 'ambiente', 'valor_total',
                    'order', 'created_at', 'autorizada_em')
    list_filter = ('status', 'ambiente', 'created_at')
    search_fields = ('chave_acesso', 'numero', 'order__id')
    date_hierarchy = 'created_at'
    readonly_fields = [f.name for f in Invoice._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
