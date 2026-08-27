from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit.services import AuditService
from apps.users.permissions import IsManager
from . import fiscal
from .models import MenuCategory, MenuItem
from .serializers import MenuCategorySerializer, MenuItemSerializer
from .services import FiscalConferenceService


class MenuCategoryViewSet(viewsets.ModelViewSet):
    queryset = MenuCategory.objects.all()
    serializer_class = MenuCategorySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['is_active']
    ordering_fields = ['display_order', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsManager()]


class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.select_related('category').all()
    serializer_class = MenuItemSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'sector', 'is_active', 'csosn', 'origem']
    search_fields = ['name', 'sku', 'ncm', 'barcode_gtin']
    ordering_fields = ['name', 'price', 'updated_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'fiscal_check']:
            return [IsAuthenticated()]
        return [IsManager()]

    def _log(self, action_name, item, details):
        AuditService.log(user=self.request.user, action=action_name, entity='MenuItem',
                         entity_id=item.id, details=details, request=self.request)

    def perform_create(self, serializer):
        item = serializer.save()
        self._log('CREATE', item, f'Item de cardápio "{item.name}" ({item.sku}) criado')

    def perform_update(self, serializer):
        item = serializer.save()
        self._log('UPDATE', item, f'Item de cardápio "{item.name}" ({item.sku}) atualizado')

    def perform_destroy(self, instance):
        self._log('DELETE', instance, f'Item de cardápio "{instance.name}" ({instance.sku}) removido')
        instance.delete()

    @action(detail=True, methods=['get'])
    def fiscal_check(self, request, pk=None):
        """Conferência fiscal de um item."""
        return Response(FiscalConferenceService.check_item(self.get_object()))

    @action(detail=False, methods=['get'], permission_classes=[IsManager])
    def fiscal_report(self, request):
        """Conferência fiscal do catálogo inteiro (itens ativos por padrão)."""
        qs = MenuItem.objects.select_related('category')
        if request.query_params.get('all') != 'true':
            qs = qs.filter(is_active=True)
        return Response(FiscalConferenceService.check_catalog(qs))

    @action(detail=False, methods=['get'])
    def ncm_suggestions(self, request):
        return Response([{'ncm': c, 'descricao': d} for c, d in fiscal.NCM_SUGESTOES])

    @action(detail=False, methods=['get'])
    def fiscal_choices(self, request):
        """Opções para os selects do formulário fiscal no frontend."""
        def opts(choices):
            return [{'value': v, 'label': l} for v, l in choices]
        return Response({
            'origem': opts(fiscal.Origem.choices),
            'csosn': opts(fiscal.CSOSN.choices),
            'cfop': opts(fiscal.CFOP.choices),
            'cst_pis_cofins': opts(fiscal.CST_PIS_COFINS.choices),
            'unidade': opts(fiscal.UnidadeMedida.choices),
            'csosn_com_st': sorted(fiscal.CSOSN_COM_ST),
            'csosn_com_icms_proprio': sorted(fiscal.CSOSN_COM_ICMS_PROPRIO),
        })
